# -*- coding: utf-8 -*-
from polib import unescape

from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import UploadedFile, SimpleUploadedFile
from django.http import HttpResponse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext as _

from authority.views import permission_denied
from actionlog.models import action_logging
from projects.models import Component
from projects.views import component_submit_file
from translations.lib.types.pot import MsgfmtCheckError
from translations.models import POFile
from txcommon.models import get_profile_or_user
from txcommon.views import json_result
from txcommon.log import logger
from submissions import submit_by_email
from webtrans.forms import TranslationForm
from webtrans.templatetags.webeditortags import webtrans_is_under_max

# Temporary
from txcommon import notifications as txnotification

# Enable Google translation suggestions
WEBTRANS_SUGGESTIONS = getattr(settings, 'WEBTRANS_SUGGESTIONS', True)

def transfile_edit(request, pofile_id, form_list):
    # TODO: Move it or part of it to a better place, probably the 'done' method
    # of the wizard
    pofile = get_object_or_404(POFile, pk=pofile_id)
    po_entries = pofile.object.trans.get_po_entries(pofile.filename)
    filename = pofile.filename
    component = pofile.object
    lang_code = pofile.language_code

    if not webtrans_is_under_max(pofile.total):
        return permission_denied(request)

    # Forms will be actually added to the form_list by the SessionWizard only 
    # if they have changed
    if form_list:
        for form in form_list:
            for fieldname in form.fields.keys():
                if 'msgid_field_' in fieldname:
                    nkey = fieldname.split('msgid_field_')[1]
                    msgstr_field = 'msgstr_field_%s' % nkey
                    fuzzy_field = 'fuzzy_field_%s' % nkey

                    if msgstr_field in form.changed_data or \
                        fuzzy_field in form.changed_data:

                        msgid_value = form.cleaned_data['msgid_field_%s' % nkey]
                        entry = po_entries.find(unescape(msgid_value))

                        #TODO: Find out why it's needed to remove it first
                        po_entries.remove(entry)

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

                        po_entries.append(entry)

        po_contents = po_entries.__str__().encode('utf-8')
        edited_file = SimpleUploadedFile(filename, po_contents)
        edited_file.targetfile = filename
        submitted_file = {filename: edited_file}
        msg = settings.DVCS_SUBMIT_MSG % {'message': request.POST['message'],
                                          'domain' : request.get_host()}

        #TODO: This code right now duplicates stuff from the submit_file view
        # in the projects app. It will be moved to a centralized place once
        # a submission orchestration layer is created
        try:

            if settings.MSGFMT_CHECK and filename.endswith('.po'):
                logger.debug("Checking %s with msgfmt -c for component %s" % 
                            (filename, component.full_name))
                component.trans.msgfmt_check(edited_file.read())

            logger.debug("Checking out for component %s" % component.full_name)
            component.prepare()

            logger.debug("Submitting %s for component %s" % 
                        (filename, component.full_name))

            if component.submission_type=='ssh' or component.unit.type=='tar':
                component.submit(submitted_file, msg, 
                                    get_profile_or_user(request.user))

            if component.submission_type=='email':
                logger.debug("Sending %s for component %s by email" % 
                            (filename, component.full_name))
                submit_by_email(component, submitted_file, request.user)

            logger.debug("Calculating %s stats for component %s" % 
                        (filename, component.full_name))

            # TODO: Find out a better way to handle it. We might wand to merge
            # the file with the POT before commiting, but it just must happen when
            # the POT is not broken for intltool based projects.
            component.trans.set_file_stats(filename, is_msgmerged=False)

            # Getting the new PO file stats after submit it
            pofile = POFile.objects.get(filename=filename,
                                        object_id=component.id)

            # To be used by the ActionLog later
            object_list = [component.project, component]
            
            ## Append the language to the ActionLog object_list if it exist for
            ## this file
            if hasattr(pofile, 'language') and pofile.language is not None:
                object_list.append(pofile.language)

            # ActionLog & Notification
            nt = 'project_component_file_submitted'
            context = {'component': component, 
                        'filename':filename, 
                        'pofile': pofile}
            action_logging(request.user, object_list, nt, context=context)
            if settings.ENABLE_NOTICES:
                txnotification.send_observation_notices_for(component.project,
                    signal=nt, extra_context=context)

            request.user.message_set.create(message=_("File submitted " 
                            "successfully: %s" % filename))

        except MsgfmtCheckError:
            logger.debug("Msgfmt -c check failed for the %s file." % filename)
            request.user.message_set.create(message=_("Your file does not"
                                    " pass by the check for correctness"
                                    " (msgfmt -c). Please run this command"
                                    " on your system to see the errors."))
        except StandardError, e:
            logger.debug("Error submiting translation file %s"
                        " for %s component: %r" % (filename,
                        component.full_name, e))
            request.user.message_set.create(message = _(
                "Sorry, an error is causing troubles to send your file."))

    else:
        request.user.message_set.create(message = _(
            "The file wasn't sent because you haven't changed anything."))

    return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(component.project.slug, component.slug,)))

