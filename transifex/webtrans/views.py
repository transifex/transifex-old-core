# -*- coding: utf-8 -*-
from polib import unescape

from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import UploadedFile, SimpleUploadedFile
from django.http import HttpResponse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext as _

from actionlog.models import action_logging
from projects.models import Component
from projects.views import component_submit_file
from translations.models import POFile
from txcommon.models import get_profile_or_user
from txcommon.views import json_result
from txcommon.log import logger
from submissions import submit_by_email

from forms import TranslationForm
from webtrans.templatetags.webeditortags import webtrans_is_under_max
from authority.views import permission_denied

# Temporary
from txcommon import notifications as txnotification

# Enable Google translation suggestions
WEBTRANS_SUGGESTIONS = getattr(settings, 'WEBTRANS_SUGGESTIONS', True)

def transfile_edit(request, pofile_id):
    pofile = get_object_or_404(POFile, pk=pofile_id)
    po_entries = pofile.object.trans.get_po_entries(pofile.filename)
    filename = pofile.filename
    component = pofile.object
    lang_code = pofile.language_code

    if not webtrans_is_under_max(pofile.total):
        return permission_denied(request)

    if request.method == "POST":
        for fieldname, value in request.POST.items():
            if 'msgid_field_' in fieldname:
                nkey = fieldname.split('msgid_field_')[1]
                if request.POST.get('changed_field_%s' % nkey, None) == 'True':
                    entry = po_entries.find(unescape(value))

                    #TODO: Find out why it's needed to remove it first
                    po_entries.remove(entry)

                    string = request.POST['msgstr_field_%s' % nkey]
                    entry.msgstr = unescape(string);

                    # Taking care of fuzzies flags
                    if request.POST.get('fuzzy_field_%s' % nkey, None):
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
            component.trans.set_stats_for_lang(lang_code, try_to_merge=False)

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

        except ValueError: # msgfmt_check
            logger.debug("Msgfmt -c check failed for the %s file." % filename)
            request.user.message_set.create(message=_("Your file does not" \
                                    " pass by the check for correctness" \
                                    " (msgfmt -c). Please run this command" \
                                    " on your system to see the errors."))
        except StandardError, e:
            logger.debug("Error submiting translation file %s"
                        " for %s component: %r" % (filename,
                        component.full_name, e))
            request.user.message_set.create(message = _(
                "Sorry, an error is causing troubles to send your file."))

        return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                    args=(component.project.slug, component.slug,)))
    else:
        form = TranslationForm(po_entries)

    return render_to_response('webtrans/transfile_edit.html', {
        'pofile': pofile,
        'pofile_form': form,
        'WEBTRANS_SUGGESTIONS': WEBTRANS_SUGGESTIONS,
    }, context_instance=RequestContext(request))
