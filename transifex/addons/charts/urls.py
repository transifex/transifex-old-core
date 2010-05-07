# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import chart_comp_image, chart_comp_html_js, chart_comp_json

urlpatterns = patterns('',
    # Provide URL for static image of chart
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/chart/image_png/$',
        view = chart_comp_image,
        name = 'chart_comp_image',),

    # Serve includable JS
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/chart/inc_js/$',
        view = chart_comp_html_js,
        name = 'chart_comp_js',
        kwargs = {"template_name": "component_chart.js"}),

    # Serve HTML code which loads JS data
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/chart/$',
        view = chart_comp_html_js,
        name = 'chart_comp_html',
        kwargs = {"template_name": "component_chart.html"}),

    # Serve JSON data for table/chart whatever
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/chart/json/$',
        view = chart_comp_json,
        name = 'chart_comp_json',),
)
