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
        step = int(request.POST.get(self.step_field_name, 0))

        # Initializing TranslationForm vars
        self.pofile = POFile.objects.get(filename=filename, component=component)
        self.po_entries = component.trans.get_po_entries(filename)
        
        # Drop obsolete entries from the list
        obsoletes = len(self.po_entries.obsolete_entries())
        if obsoletes > 0:
            self.po_entries_list = self.po_entries[:-obsoletes]
        else:
            self.po_entries_list = self.po_entries

        # Initializing TransFormWizard vars
        self.key =  md5_constructor('%s%s%s' % 
            (request.user.pk, component.pk, self.pofile.pk)).hexdigest()
        self.form_list = [TranslationForm for c in chunks(self.po_entries_list, 
            self.ENTRIES_PER_PAGE)]

        self.extra_context.update({'pofile': self.pofile, 
            'po_entries': self.po_entries_list, 
            'ENTRIES_PER_PAGE': self.ENTRIES_PER_PAGE,
            'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS,
            'toggle_occurrences': request.POST.get('toggle_occurrences', None),
            #'only_translated': request.POST.get('only_translated', None),
            #'only_fuzzy': request.POST.get('only_fuzzy', None),
            #'only_untranslated': request.POST.get('only_untranslated', None),
            'initial_entries_count':(self.next_step(request, step) * 
                                     self.ENTRIES_PER_PAGE),
            })

        super(TransFormWizard, self).init(request)

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
            self.store(step, request.POST, request.FILES)
            form = self.form_for(step)
            # Validate the form whenever a POST is sent, it includes the
            # navegation between the pages
            if not form.is_valid():
                return self.render(request, step, form)
            # Submit whenever the 'submit' button is pressed
            if 'submit' in request.POST:
                return self.finish(request)
            return self.render(request, self.next_step(request, step))
        return self.render(request, step)

    def get_template(self, step):
        return 'webtrans/transfile_edit.html'

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

    def make_form(self, step, data=None, files=None):
        """Create the default form for step."""
        prefix = self.get_prefix(step)
        if step in self.initial:
            initial = self.initial[step]
        else:
            initial = None
        
        # Get po entries for the chuck in a specific possition (step)
        po_entries = specific_chunk(self.po_entries_list, step, self.ENTRIES_PER_PAGE)

        # Return the form instance initialized with the data populated from the,
        # case the form for this step was already displayed
        return self.form_list[step](po_entries, data=data, files=files, 
            prefix=prefix, initial=initial)

    def finish(self, request):
        """
        Called when submitting the wizard, this method identifies the forms that
        are valid and that some field has changed, putting those in a list and 
        calling the method ``done``.
        """
        valid_forms = []
        forms = [self.form_for(step) for step in range(self.num_steps())]
        for form in forms:
            if form.is_valid() and form.has_changed():
                valid_forms.append(form) 
        return self.done(request, valid_forms)

    def done(self, request, form_list):
        """
        Method responsible for handling the final list of validated forms, that
        actually have changed, after submitting the wizard.
        """
        from projects.views.component import component_submit_file

        project_slug = self.pofile.object.project.slug
        component_slug = self.pofile.object.slug
        filename = self.pofile.filename

        for form in form_list:
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
                            entry.msgstr = unescape(msgstr_value);
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

        if form_list:
            po_contents = self.po_entries.__str__().encode('utf-8')
            edited_file = SimpleUploadedFile(filename, po_contents)
            result_view = component_submit_file(request=request, 
                project_slug=project_slug, component_slug=component_slug, 
                filename=filename, submitted_file=edited_file)
        else:
            request.user.message_set.create(message = _(
                "Nothing was sent because you haven't changed anything in the "
                "translation form."))
            return HttpResponseRedirect(reverse('projects.views.component_detail', 
                args=(project_slug, component_slug)))

        self.clear_storage(request)
        return result_view
