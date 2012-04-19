#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re
import glob
from codecs import BOM

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py

from transifex.txcommon import version

readme_file = open(u'README.rst')
long_description = readme_file.read()
readme_file.close()
if long_description.startswith(BOM):
    long_description = long_description.lstrip(BOM)
long_description = long_description.decode('utf-8')

package_data = {
    '': ['LICENCE', 'README.rst'],
    'transifex': ['transifex/static/*.*']
}

def get_requirements(filename):
    """
    Read requirements and dependency links from a file passed by parameter
    and return them as two lists in a tuple.
    """
    def add_dependency_link(line):
        link = re.sub(r'\s*-[ef]\s+', '', line)
        filename = os.path.basename(link.split('://')[1])
        url = link.split(filename)[0]
        if url not in dependency_links:
            dependency_links.append(url)

    requirements = []
    dependency_links = []
    for line in open(filename, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            # TODO support version numbers
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
            add_dependency_link(line)
        elif re.match(r'\s*-f\s+', line):
            add_dependency_link(line)
        else:
            requirements.append(line)
    return requirements, dependency_links

requirements, dependency_links = get_requirements('requirements.txt')

def buildlanguages():
    import django.core.management.commands.compilemessages as c
    oldpath = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__FILE__), 'transifex',
        'locale'))
    c.compile_messages()
    os.chdir(oldpath)

class build_py(_build_py):
    def run(self):
        buildlanguages()
        _build_py.run(self)

setup(
#    cmdclass={
#        'build_py': build_py,
#    },
    name="transifex",
    version=version,
    description="The software behind Transifex.net, the open service to collaboratively translate software, documentation and websites.",
    long_description=long_description,
    author="The Transifex community and the staff of Indifex",
    author_email="transifex-devel@googlegroups.com",
    url="http://transifex.org/",
    license="GPLv2",
    install_requires=requirements,
    dependency_links=dependency_links,
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    package_data = package_data,
    keywords = (
        'django.app',
        'translation localization internationalization vcs',),
    classifiers = [line for line in '''
Development Status :: 5 - Production/Stable
Environment :: Web Environment
Framework :: Django
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Localization
Topic :: Software Development :: Internationalization
#84 Natural Language :: Catalan
#84 Natural Language :: Chinese (Simplified)
Natural Language :: English
#84 Natural Language :: German
#84 Natural Language :: Greek
#84 Natural Language :: Hungarian
#84 Natural Language :: Italian
#84 Natural Language :: Macedonian
#84 Natural Language :: Malay
#84 Natural Language :: Persian
Natural Language :: Polish
#84 Natural Language :: Portuguese (Brazilian)
#84 Natural Language :: Romanian
#84 Natural Language :: Russian
#84 Natural Language :: Slovak
#84 Natural Language :: Spanish
#84 Natural Language :: Swedish'''.strip().split('\n')
        if not line.startswith('#')
    ],
)
