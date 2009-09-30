from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.hashcompat import md5_constructor

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

        # Quering the respective database objects
        component = get_object_or_404(Component, slug=component_slug,
                                      project__slug=project_slug)
        pofile = POFile.objects.get(filename=filename, component=component)
        po_entries = component.trans.get_po_entries(filename)

        # Initializing TranslationForm vars
        self.po_id = pofile.pk
        # Drop obsolete entries from the list
        obsoletes = len(po_entries.obsolete_entries())
        if obsoletes > 0:
            self.po_entries = po_entries[:-obsoletes]
        else:
            self.po_entries = po_entries

        # Initializing TransFormWizard vars
        self.key =  md5_constructor('%s%s%s' % 
            (request.user.pk, component.pk, pofile.pk)).hexdigest()
        self.form_list = [TranslationForm for c in chunks(self.po_entries, 
            self.ENTRIES_PER_PAGE)]

        self.extra_context.update({'pofile': pofile, 
            'po_entries': self.po_entries, 
            'ENTRIES_PER_PAGE': self.ENTRIES_PER_PAGE,
            'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS,
            'toggle_occurrences': request.POST.get('toggle_occurrences', None),
            #'only_translated': request.POST.get('only_translated', None),
            #'only_fuzzy': request.POST.get('only_fuzzy', None),
            #'only_untranslated': request.POST.get('only_untranslated', None),
            'initial_entries_count':(self.next_step(request) * self.ENTRIES_PER_PAGE),
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

    def next_step(self, request, step=0):
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
        initial = self.initial[step] if step in self.initial else None
        
        # Get po entries for the chuck in a specific possition (step)
        po_entries = specific_chunk(self.po_entries, step, self.ENTRIES_PER_PAGE)

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
        from webtrans.views import transfile_edit
        webtrans_view = transfile_edit(request, self.po_id, form_list)
        self.clear_storage(request)
        return webtrans_view
