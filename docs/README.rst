
=========================
 Transifex Documentation
=========================

Welcome to the Transifex documentation.

The docs are available in the following formats:

- Plaintext: Suitable for printing, reading from the command-line etc.

- HTML: A rich rendering of the docs is also available in HTML format, with
  inter-links, nice formatting, searching, automatic indexing etc. Just fire
  up your browser and point it at the 'html/' directory.

Instructions on how to build the docs can be found in the README file inside
the '_devel/' directory.


Environment
-----------

In order to use and update the documentation of transifex, you have to set up
a python environment where sphinx is available. Because we are using the github
pages to publish the content, you have to make some extra configuration in order
to be able to push the changes. The simplest setup is the following:

- First of all, create a new directory named docs. This directory will hold everything,
  from the source files, to the generated markup.
- Inside docs clone this repository twice. The first time in a directory named master,
  and the second time in a directory named gh-pages.
- Finally, navigate to the gh-pages directory and checkout the gh-pages branch.

Now everything should be ready. When you are ready to update the docs, go in the
gh-pages, commit the changes of the html documents, and push. Use extra caution
not to force-push. That way some docs could be lost.

That's it. Your changes are live. \o/
