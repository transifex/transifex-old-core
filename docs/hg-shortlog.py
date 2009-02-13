#!/usr/bin/env python
# Produces shortlog from hg log output.
#
# hg log --template "{author|person}\t{author|email}\t{desc|firstline}\n"
#
# e.x. 
# Dimitris Glezos<tab>dimitris@glezos.com<tab>Contributions by Silvio Pierro

import os
import re
import sys
from collections import defaultdict
from optparse import OptionParser

# Save the invocation name of the script, for later use.
progname = os.path.basename(sys.argv[0])

# The regular expression matcher for parsing shortlog output lines.
log_re = None

def message(msg=None):
    """Print an optional `msg' message string to our standard error
    stream.  Note that a newline is appended automatically to the
    message string, as if it was displayed with print(), and no
    exceptions are captured by message()."""
    if msg:
        s = "%s\n" % (msg)
        sys.stderr.write(s)
        sys.stderr.flush()
    return None

def error(code, msg=None):
    """Print `msg' as an optional error message string, and die with an
    error of `code'."""
    if msg:
        s = '%s: error: %s' % (progname, msg)
        message(s)
    sys.exit(code)

def warning(msg=None):
    """Print `msg' as an optional warning string."""
    if msg:
        s = '%s: warning: %s' % (progname, msg)
        message(s)
    return None

def read_mailmap(filename):
    """
    Reads mailmap file
    Returns {<email>:<name>} dict
    """
    mailmap_re = re.compile('^(?P<name>.*) \<(?P<email>.*)\>')
    mailmap = {}

    f = open(filename,'r')
    try:
        for line in f:
            if line.startswith('#'):
                continue
            m = mailmap_re.match(line)
            if m:
                mailmap[m.group('email')] = m.group('name')
    finally:
        f.close()
    return mailmap

def log():
    """ Yields (name, email, msg) from stdin"""

    for line in sys.stdin:
        m = log_re.match(line)
        if m:
            g = m.group
            yield g('name'), g('email'), g('msg')

def get_commit_map(mailmap={}):
    """
    Returns {<Full Name> : [<msg1>, <msg2>]} dict
    """
    if not log_re:
        warning("No log matcher")
        return None
    commit_map = defaultdict(list)
    for name, email, msg in log():
        # search mailmap for the email. Use name if you don't find it
        name = mailmap.get(email, name)
        commit_map[name].append(msg)
    return commit_map

if __name__ == "__main__":
    try:
        log_re = re.compile('^(?P<name>.*)\t(?P<email>.*)\t(?P<msg>.*)$')
    except Exception, inst:
        error(1, "invalid regular expression %s" % str(inst))

    parser = OptionParser()
    parser.add_option('-m', '--mailmap', default='.mailmap', dest='mailmap',
        help="Use mailmap file")
    parser.add_option('-n', '--no-mailmap', action='store_false', dest='mailmap',
        help="Don't use mailmap")
    (options, args) = parser.parse_args()

    if options.mailmap:
        options.mailmap = read_mailmap(options.mailmap)
    commit_map = get_commit_map(mailmap=options.mailmap or {})
    if not commit_map:
        error(1, "No commits")
    for person, commits in commit_map.iteritems():
        print '%s (%s):' % (person, len(commits))
        for commit in commits:
            print '\t%s' % commit
    sys.exit(0)
