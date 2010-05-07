# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Count
from projects.models import Component, Project
from projects.permissions import pr_project_private_perm
from translations.models import POFile
from txcommon.context_processors import site_url_prefix_processor
from txcommon.decorators import one_perm_required_or_403

# For interactive charts:
import gviz_api

# For image charts:
from pygooglechart import StackedHorizontalBarChart, Axis

def get_top(obj):
    """
    Returns first 14 virtual POFiles in sorted order
    """
    def compare(a,b):
        if a.trans_perc < b.trans_perc:
            return 1
        return -1
    return sorted(obj.get_stats(), compare)[:14]

def get_image_url(obj):
    """
    Returns URL for the static image
    """
    pofiles = get_top(obj)
    height = 210

    trans = []
    fuzzy = []
    labels_left = []
    labels_right = []
    
    for pofile in pofiles:
        trans.append(pofile.trans_perc)
        fuzzy.append(pofile.fuzzy_perc)
        labels_left.append(pofile.lang_or_code)
        labels_right.append("%s%%" % pofile.trans_perc)

    labels_left.reverse()
    labels_right.reverse()

    chart = StackedHorizontalBarChart(
        width = 350,
        height = 14 + 13 * len(pofiles),
        x_range=(0, 100))
    chart.set_bar_width(9)
    chart.set_colours(['78dc7d', 'dae1ee', 'efefef']) # Green, dark gray, light gray
    chart.set_axis_labels(Axis.LEFT, labels_left)
    chart.set_axis_labels(Axis.RIGHT, labels_right)
#    chart.set_title("Project: %s" % (pofile.object.project.name))
    chart.add_data(trans)
    chart.add_data(fuzzy)
    return chart.get_url()

def get_gviz_json(obj):
    """
    Returns JSON data of Google Visualization API
    """
    pofiles = get_top(obj)
    description = { "lang": ("string", "Language"),
                    "trans": ("number", "Translated"),
                    "fuzzy": ("number", "Fuzzy"),}
    data = []
    for pofile in pofiles:
        data.append({
            "lang": pofile.lang_or_code,
            "trans":pofile.trans_perc,
            "fuzzy":pofile.fuzzy_perc})
    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    return data_table.ToJSonResponse(         
        columns_order=("lang", "trans", "fuzzy"))

def chart_comp_image(request, project_slug, component_slug):

    component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)
    if component.project.private:
        raise PermissionDenied
    return HttpResponseRedirect(get_image_url(component))

def chart_comp_html_js(request, project_slug, component_slug, template_name=None):
    if not template_name:
        raise Http404
    component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)
    if component.project.private:
        raise PermissionDenied
    return render_to_response(template_name,
        {   "project" : component.project,
            "component" : component, },
        RequestContext(request, {}, [site_url_prefix_processor]))

def chart_comp_json(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)
    if component.project.private:
        raise PermissionDenied
    return HttpResponse(content = get_gviz_json(component))
