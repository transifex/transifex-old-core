from polib import unescape
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.hashcompat import md5_constructor
from django.utils.translation import ugettext as _

from projects.models import Component
from translations.models import POFile
from txcommon.formtools.wizards import SessionWizard
from webtrans.forms import TranslationForm

def chunks(clist, crange):
    """Yield successive crange-sized chunks from clist."""
    for i in xrange(0, len(clist), crange):
        yield clist[i:i+crange]

def specific_chunk(clist, cindex, crange):
    """Return a specific chunk of a list of crange-sized chunks from clist."""
    for i, chunk in enumerate(chunks(clist, crange)):
        if i == cindex:
            return chunk

def has_string(entry, string):
    """Return True if string is found in any attr of the po entry."""
    if string in entry.msgid:
        return True
    if entry.msgid_plural:
        if string in entry.msgid_plural:
            return True
        for value in entry.msgstr_plural.values():
            if string in value:
                return True
    else:
        if string in entry.msgstr:
            return True


class TransFormWizard(SessionWizard):

    ENTRIES_PER_PAGE = settings.WEBTRANS_ENTRIES_PER_PAGE

    def __name__(self, request):
        return "TransFormWizard"

    def init(self, request, *args, **kwargs):
        """
        Method used for initialize things.

        This method is the first method called in __call__() which acts like a
        view and has access to the url args by accessing the *args and **kwargs
        parameters.

        """
        # Get parameters form the URL
        project_slug = kwargs['project_slug']
        component_slug = kwargs['component_slug']
        filename = kwargs['filename']

        component = get_object_or_404(Component, slug=component_slug,
                                      project__slug=project_slug)
        pofile = get_object_or_404(POFile, filename=filename, component=component)
        self.step = int(request.POST.get(self.step_field_name, 0))

        # Getting session
        self.key =  md5_constructor('%s%s%s' % 
            (request.user.pk, component.pk, pofile.pk)).hexdigest()
        self._storage = request.session.setdefault(self.key, {})

        # Initializing TranslationForm vars
        self.pofile = pofile
        self.po_entries = self.get_stored_po_entries()
        if not self.po_entries:
            self.po_entries = component.trans.get_po_entries(filename)
            self.po_entries_changed = False
        else:
            self.po_entries_changed = True

        # Get stored filters
        f = self.get_stored_filters()

        # Getting filtering settings
        if f:
            self.only_translated = f.get('only_translated', None)
            self.only_fuzzy = f.get('only_fuzzy', None)
            self.only_untranslated = f.get('only_untranslated', None)
            self.string = f.get('string', '')
        else: # Default values
            self.only_translated = False
            self.only_fuzzy = True
            self.only_untranslated = True
            self.string = ''
            self.store_filters(self.only_translated, self.only_fuzzy, 
                self.only_untranslated, self.string)

        # Getting po_entries based on the filter settings
        self.po_entries_list = self.filter_po_entries()
        
        if 'extra_context' in kwargs:
            self.extra_context.update(kwargs['extra_context'])


    def __call__(self, request, *args, **kwargs):
        """
        This method acts like a view.

        It was necessary to change a bit the normal behavior of this method,
        due the fact we only want to validate step forms displayed to the users 
        and, also, to be able to submit the form without pass throught all the 
        steps.

        """
        self.init(request, *args, **kwargs)

        step = self.current_step(request)
        if request.method == 'POST':
            
            # Store the data and files for the related step right away
            self.store(step, request.POST, request.FILES)
            
            # Get the form instance
            form = self.form_for(step)
            
            # Validate the current form
            if not form.is_valid():
                return self.render(request, step, form)

            # In case it changed, store the entire updated pofile in the session
            if form.has_changed():
                self.update_po_entries(form)
                self.store_po_entries(self.po_entries)

            # Submit whenever the 'submit_file' or 'submit_for_review' button 
            # are pressed
            if 'submit_file' in request.POST or \
                'submit_for_review' in request.POST:
                return self.done(request)

            return self.render(request, self.next_step(request, step))
        return self.render(request, step)

    def get_template(self, step):
        return 'webtrans/transfile_edit.html'

    def num_steps(self):
        """Total number of steps in the wizard."""
        return len(list(chunks(self.po_entries_list, self.ENTRIES_PER_PAGE)))

    def next_step(self, request, step):
        """Given the request and the current step, calculate the next step."""
        if 'next' in request.POST:
            return step + 1
        # Added verifying for current_page field, used for the pagination
        if 'current_page' in request.POST:
            return int(request.POST['current_page'])-1
        if 'previous' in request.POST:
            return step - 1
        return step

    def form_for(self, step):
        """
        Get the data out of storage and return a form for it, or, if no data is 
        in storage for this step, create the default form.
        """
        if 'steps' in self._storage:
            data, files = self._storage['steps'].get(step, (None, None))
        else: 
            data, files = (None, None)
        return self.make_form(step, data, files)

    def make_form(self, step, data=None, files=None):
        """Create a form for step based on the filtered po_entries_list."""
        prefix = self.get_prefix(step)
        if step in self.initial:
            initial = self.initial[step]
        else:
            initial = None

        # Get po_entries for the chuck in a specific possition (step)
        po_entries = specific_chunk(self.po_entries_list, step, self.ENTRIES_PER_PAGE)

        # Return the form instance initialized with the data populated, in case
        # it was passed by parameter
        return TranslationForm(po_entries, data=data, files=files, 
            prefix=prefix, initial=initial)

    def filter_po_entries(self):
        """Filter the po_entries based on the parameters."""

        # Drop obsolete entries from the list
        ob = len(self.po_entries.obsolete_entries())
        if ob == 0:
            entries = self.po_entries
        else:
            entries = self.po_entries[:-ob]

        # Filtering
        po_entries_list = []
        for entry in entries:
            if self.string and not has_string(entry, self.string):
                continue
            if entry.translated():
                if self.only_translated:
                    po_entries_list.append(entry)
            elif 'fuzzy' in entry.flags:
                if self.only_fuzzy:
                    po_entries_list.append(entry)
            elif entry.msgstr == '':
                if self.only_untranslated:
                    po_entries_list.append(entry)
        return po_entries_list

    def store_filters(self, only_translated, only_fuzzy, only_untranslated, string):
        """Store the filter options in the session."""
        self._storage['filters'] = {'only_translated': only_translated,
                                    'only_fuzzy': only_fuzzy,
                                    'only_untranslated': only_untranslated,
                                    'string': string,}

    def get_stored_filters(self):
        """Get the stored filter options from the session."""
        if self._storage:
            return self._storage.get('filters', None)

    def store_po_entries(self, po_entries):
        """Store the po_entries in the session."""
        self._storage['po_entries'] = po_entries
        self.po_entries_changed = True

    def get_stored_po_entries(self):
        """Get the po_entries stored from the session."""
        if self._storage:
            return self._storage.get('po_entries', None)

    def update_po_entries(self, form):
        """
        Update po_entries, which is a polib.POFile object, with the changed 
        form data.
        """
        for fieldname in form.fields.keys():
            if 'msgid_field_' in fieldname:
                nkey = fieldname.split('msgid_field_')[1]
                msgstr_field = 'msgstr_field_%s' % nkey
                fuzzy_field = 'fuzzy_field_%s' % nkey

                if msgstr_field in form.changed_data or \
                    fuzzy_field in form.changed_data:

                    msgid_value = form.cleaned_data['msgid_field_%s' % nkey]
                    entry = self.po_entries.find(unescape(msgid_value))

                    msgstr_value = form.cleaned_data['msgstr_field_%s' % nkey]
                    try:
                        entry.msgstr = unescape(msgstr_value)
                    except AttributeError:
                        for i, value in enumerate(msgstr_value):
                            entry.msgstr_plural['%s' % i]=unescape(value)

                    # Taking care of fuzzies flags
                    if form.cleaned_data.get('fuzzy_field_%s' % nkey, None):
                        if 'fuzzy' not in entry.flags:
                            entry.flags.append('fuzzy')
                    else:
                        if 'fuzzy' in entry.flags:
                            entry.flags.remove('fuzzy')

    def store(self, step, data, files):
        """
        Store the data that was sent to a step.
        """
        if 'steps' in self._storage:
            self._storage['steps'].update({step: (data, files)})
        else:
            self._storage['steps'] = {step: (data, files)}

    def render(self, request, step, form=None, context=None):
        """
        Called to render a specific step.
        You may pass 'form' manually in case you want a form that has been error-checked.
        If you don't give 'form', it will be retreived from storage.
        """
        # Get filter settings from the form
        if request.method == 'POST' and not form:
            only_translated = request.POST.get('only_translated', None)
            only_fuzzy = request.POST.get('only_fuzzy', None)
            only_untranslated = request.POST.get('only_untranslated', None)
            string = request.POST.get('string', None)

            # If filter changed
            if only_translated != self.only_translated or \
                only_fuzzy != self.only_fuzzy or \
                only_untranslated  != self.only_untranslated or \
                string != self.string:

                self.only_translated = only_translated
                self.only_fuzzy = only_fuzzy
                self.only_untranslated = only_untranslated
                self.string = string

                # Store the current filters
                self.store_filters(self.only_translated, self.only_fuzzy, 
                    self.only_untranslated, self.string)

                if 'steps' in self._storage:
                    del self._storage['steps']

                # Getting po_entries based on the filter settings
                self.po_entries_list = self.filter_po_entries()

                # Make sure the current page is never greater than the total 
                # number of pages of the wizard
                nsteps = self.num_steps() - 1
                if step > nsteps:
                    if nsteps > 0:
                        step = nsteps
                    else:
                        step = 0

        self.extra_context.update({'pofile': self.pofile, 
            'po_entries': self.po_entries_list, 
            'ENTRIES_PER_PAGE': self.ENTRIES_PER_PAGE,
            'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS,
            'toggle_contexts': request.POST.get('toggle_contexts', None),
            'only_translated': self.only_translated,
            'only_fuzzy': self.only_fuzzy,
            'only_untranslated': self.only_untranslated,
            'string': self.string,
            'initial_entries_count':(self.next_step(request, self.step) * 
                                     self.ENTRIES_PER_PAGE),
            })

        self.save_step(step)
        self.commit_storage(request)
        context = context or {}
        context.update(self.extra_context)
        return render_to_response(self.get_template(step), dict(context,
            step0=step,
            step=step + 1,
            step_count=self.num_steps(),
            form=form or self.form_for(step),
        ), context_instance=RequestContext(request))

    def done(self, request):
        """
        Method responsible for handling the final submittion of the wizard.
        """
        from projects.views.component import component_submit_file

        project_slug = self.pofile.object.project.slug
        component_slug = self.pofile.object.slug
        filename = self.pofile.filename

        if self.po_entries_changed:
            po_contents = self.po_entries.__str__().encode('utf-8')
            edited_file = SimpleUploadedFile(filename, po_contents)
            result_view = component_submit_file(request=request, 
                project_slug=project_slug, component_slug=component_slug, 
                filename=filename, submitted_file=edited_file)
        else:
            request.user.message_set.create(message = _(
                "Nothing was sent because you haven't changed anything in the "
                "translation form."))
            return HttpResponseRedirect(reverse('component_detail',
                args=(project_slug, component_slug,)))

        self.clear_storage(request)
        return result_view
