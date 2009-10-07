# Picked from http://code.djangoproject.com/ticket/9200#comment:14
from django import forms
from django.shortcuts import render_to_response
from django.template.context import RequestContext

class SessionWizard(object):
    # Dictionary of extra template context variables.
    extra_context = {}

    # The HTML (and POST data) field name for the "step" variable.
    step_field_name = 'wizard_step'

    def __init__(self, key, form_list, initial=None):
        """
        'key' is the name where data will be stored in the session. Should be unique.
        'form_list' should be a list of Form classes, not instances.
        'initial' may be a list of dicts or a dict of dicts maping step to initial data.
        """
        self.key = key
        self.form_list = form_list
        self.initial = initial or ()

    def __repr__(self):
        return 'key: %s\nform_list: %s\ninitial_data: %s' % (self.step, self.form_list, self.initial)

    def __call__(self, request, *args, **kwargs):
        """Acts like a view"""
        self.init(request, *args, **kwargs)
        step = self.current_step(request)
        if request.method == 'POST':
            self.store(step, request.POST, request.FILES)
            form = self.form_for(step)
            if self.lingers_on(step) and not form.is_valid():
                return self.render(request, step, form)
            if self.is_last(step):
                return self.finish(request)
            return self.render(request, self.next_step(request, step))
        return self.render(request, step)

    def num_steps(self):
        """Total number of steps in the form list."""
        return len(self.form_list)

    def is_last(self, step):
        """
        Called after step 'step' is completed to determine whether or not
        the form wizard is finished
        """
        return step + 1 == self.num_steps()

    def lingers_on(self, step):
        """
        Called when the form at step 'step' does not validate.
        If a true value is returned, the form at step 'step' will be redisplayed with
        error messages. If a false value is returned, the user is allowed to move on.
        This method determines whether or not a user can leave a page with incomplete
        data and come back later.
        Regardless of the decision of this method, all forms must validate before
        the formwizard can be completed.

        By default, if 'tried_finishing' is set, the formset lingers.
        """
        return hasattr(self, 'tried_finishing')

    def get_prefix(self, step):
        """
        Allows specific prefix calculation per form. Because forms are session based,
        no prefix is required. Return None to use no prefix.
        """
        return None

    def current_step(self, request):
        """
        Retrieve the current step of computation.
        By default, looks in POST first and saved_step second.
        """
        return int(request.POST.get(self.step_field_name, self.saved_step()))

    def saved_step(self):
        """
        Return the most recently viewed page so that the wizard may be
        resumed where the user left off, even if they navigated away.
        """
        return self._storage.setdefault('step', 0)

    def save_step(self, step):
        """
        Save 'step' in a fashion reversable by 'saved_step'.
        Called just before page 'step' is rendered.
        """
        self._storage['step'] = step

    def next_step(self, request, step):
        """
        Given the request and the current step, calculate the next step
        """
        if 'next' in request.POST:
            return step + 1
        if 'previous' in request.POST:
            return step - 1
        return step

    def init(self, request, *args, **kwargs):
        """
        Initialize the storage. This method is called with all extra arguments
        given to the view, so any other initialization should be done here.
        """
        if 'extra_context' in kwargs:
            self.extra_context.update(kwargs['extra_context'])
        self._storage = request.session.setdefault(self.key, {})

    def commit_storage(self, request):
        """
        Ensure that data gets saved to the session before the view terminates.
        """
        request.session[self.key] = self._storage

    def clear_storage(self, request):
        """Clear all trace of the formwizard from the session."""
        del request.session[self.key]

    def store(self, step, data, files):
        """
        Store the data that was sent to a step.
        """
        # NOTE: we must save the POST and FILE data instead of the form,
        # because forms don't always pickle nicely.
        self._storage[step] = (data, files)

    def form_for(self, step):
        """
        Get the data out of storage and return a form for it, or, if no
        data is in storage for this step, create the default form.
        """
        if step in self._storage:
            data, files = self._storage[step]
        else: 
            data, files = (None, None)
        return self.make_form(step, data, files)

    def make_form(self, step, data=None, files=None):
        """ Create the default form for step.  """
        prefix = self.get_prefix(step)
        if step in self.initial:
            initial = self.initial[step]
        else:
            initial = None
        return self.form_list[step](data, files, prefix=prefix, initial=initial)

    def finish(self, request):
        """
        Called when the formset may be done (when is_last returns True)
        Renders the first invalid form in order of step,
        or calls 'done' if all forms are valid.
        """
        self.tried_finishing = True
        forms = [self.form_for(step) for step in range(self.num_steps())]
        for i, form in enumerate(forms):
            if not form.is_valid():
                return self.render(request, i, form)
        return self.done(request, forms)

    def done(self, request, form_list):
        raise NotImplementedError('Your %s class has not defined a done() method, which is required.' % self.__class__.__name__)

    def get_template(self, step):
        return 'forms/wizard.html'

    def render(self, request, step, form=None, context=None):
        """
        Called to render a specific step.
        You may pass 'form' manually in case you want a form that has been error-checked.
        If you don't give 'form', it will be retreived from storage.
        """
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
