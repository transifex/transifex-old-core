# -*- coding: utf-8 -*-

HELP = """
Transifex client application

Available commands:

  init - Initialize Transifex configuration in specified directory
  push - Push strings to Transifex server
  pull - Pull strings from Transifex server
"""

from libtransifex import core as tx
import os
import sys

reload(sys) # WTF? Otherwise setdefaultencoding doesn't work

# When we open file with f = codecs.open we specifi FROM what encoding to read
# This sets the encoding for the strings which are created with f.read()
sys.setdefaultencoding('utf-8')


from libtransifex.core import ParseError, CompileError
from libtransifex.qt import LinguistParser # Qt4 TS files
from libtransifex.java import JavaPropertiesParser # Java .properties
from libtransifex.apple import AppleStringsParser # Apple .strings
#from libtransifex.ruby import YamlParser # Ruby On Rails (broken)
#from libtransifex.resx import ResXmlParser # Microsoft .NET

parsers = [LinguistParser, JavaPropertiesParser, AppleStringsParser] #, ResXmlParser, YamlParser]

def find_dot_tx(path = os.getcwd()):
    if path == "/":
        return None
    joined = os.path.join(path, ".tx")
    if os.path.isdir(joined):
        return joined
    else:
        return find_dot_tx(os.path.dirname(path))
    
if len(sys.argv) <= 1:
    print HELP
    exit(1)

config = find_dot_tx()
if not config:
    print "Couldn't find any .tx directory!"
    exit(2)

txroot = os.path.dirname(config)
cmd = sys.argv[1]

from urllib import urlencode
import httplib
conn = httplib.HTTPConnection("localhost:8000")
if cmd == "scan":
    print "Scanning in: %s" % txroot
    for root, dirs, files in os.walk(txroot):
        for filename in files:
          fullname = os.path.join(root, filename)
          for parser in parsers:
                if parser.accept(fullname):
                    relpath = fullname[len(txroot):]
                    print "File %s accepted by %s" % (relpath, parser.name)

                    
                    
                    try:
                        stringset = parser.open(filename = relpath, root = txroot)                      
                        #body = stringset.to_json()
                        #headers = { 'Content-Type' : 'application/json' }
                        #conn.request("POST", "/api/projects/1/resources/1/", body, headers)
                        #resp = conn.getresponse()
                        #print resp.status, resp.reason
                        #if resp.status == 500 or resp.status == 400:
                            #data = resp.read()
                            #print data
                            #exit(1)
                    except ParseError, err:
                        print "Failed to parse %s: %s" % (fullname, err)
                        continue


                    b = parser.compile(stringset)
                    refpoint = parser.parse(b)
                    if set(stringset.strings) != set(refpoint.strings):
                        raise CompileError("Stringsets are not equivalent")

                    print "Successfully parsed: %s" % fullname