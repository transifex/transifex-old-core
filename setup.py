#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
from codecs import BOM

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py

from transifex.txcommon import version

readme_file = open(u'README')
long_description = readme_file.read()
readme_file.close()
if long_description.startswith(BOM):
    long_description = long_description.lstrip(BOM)
long_description = long_description.decode('utf-8')

package_data = {
    '': ['LICENCE', 'README'],
}

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
    description="A platform for distributed translation submissions",
    long_description=long_description,
    author="The Transifex community and the staff of Indifex",
    author_email="transifex-devel@googlegroups.com",
    url="http://transifex.org/",
    license="GPLv2",
    dependency_links = [
        "http://dist.repoze.org/",
        "http://www.aeracode.org/releases/south/",
        "http://transifex.org/files/deps/",
        "http://pypi.python.org/simple",
    ],
    setup_requires = [
        "Django >= 1.0",
        "Pygments >= 0.9",
        "Sphinx >= 0.4.2",
    ],
    install_requires = [
        "Django >= 1.0",
        "urlgrabber",
        "markdown",
        "userprofile",
        "httplib2",
        "polib >= 0.4.2",
        "Pygments >= 0.9",
        "PIL == 1.1.6",
        "contact_form >= 0.3", # hg 97559a887345 or newer
        "django-notification >= 0.1.2",
        "django-pagination >= 1.0.5",
        "tagging >= 0.3_pre",
        "django-authority",
        "django-piston",
        "South >= 0.6-rc1",
    ],
    data_files=[
        ('templates', glob.glob('transifex/templates/*.html')),
    ],

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
