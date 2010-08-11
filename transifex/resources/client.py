# -*- coding: utf-8 -*-

HELP = """
Transifex client application

Available commands:

  init - Initialize Transifex configuration in specified directory
  push - Push strings to Transifex server
  pull - Pull strings from Transifex server
"""

import os
import sys
import re
import httplib
import mimetypes
import urllib2


reload(sys) # WTF? Otherwise setdefaultencoding doesn't work

# When we open file with f = codecs.open we specifi FROM what encoding to read
# This sets the encoding for the strings which are created with f.read()
sys.setdefaultencoding('utf-8')


from libtransifex import core as tx
from libtransifex.core import ParseError, CompileError
from libtransifex.qt import LinguistParser # Qt4 TS files
from libtransifex.java import JavaPropertiesParser # Java .properties
from libtransifex.apple import AppleStringsParser # Apple .strings
#from libtransifex.ruby import YamlParser # Ruby On Rails (broken)
#from libtransifex.resx import ResXmlParser # Microsoft .NET (not finished)
#from libtransifex.pofile import PofileParser # GNU Gettext .PO/.POT parser (not started)

parsers = [LinguistParser, JavaPropertiesParser, AppleStringsParser] #, ResXmlParser, YamlParser]

from json import loads as parse_json, dumps as compile_json

class ResourceError(StandardError):
    pass

def parse_tx_url(url):
    m = re.match("(?P<hostname>https?://(\w|\.|:)+)/happix/project/(?P<project>(\w|-)+)/", url)
    if m:
        hostname = m.group('hostname')
        project = m.group('project')
        print "Transifex instance:", hostname
        print "Project slug:", project
        return hostname, project
    else:
        print "Couldn't parse pull/push URL!"
        exit(1)
    
def post_multipart(host, selector, fields, files):
    def encode_multipart_formdata(fields, files):
        LIMIT = '----------lImIt_of_THE_fIle_eW_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: application/octet-stream')
            L.append('')
            L.append(value)
        L.append('--' + LIMIT + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % LIMIT
        return content_type, body
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    buf = h.file.read()
    if errcode == 500:
        print buf
    return buf

class Project():
    def __init__(self):
        def find_dot_tx(path = os.getcwd()):
            if path == "/":
                return None
            joined = os.path.join(path, ".tx")
            if os.path.isdir(joined):
                return path
            else:
                return find_dot_tx(os.path.dirname(path))
        self.root = find_dot_tx()
        if not self.root:
            print "Couldn't find any .tx directory!"
        self.config_file = os.path.join(self.root, ".tx", "config")
        try:
            self.config = parse_json(open(self.config_file).read())
        except Exception, err:
            print "WARNING: Couldn't open/parse .tx/config file", err
            self.config = {}

        if not "resources" in self.config:
            self.config['resources'] = {}
        if len(self.config['resources']) == 0:
            self.config['resources']['master'] = {'regex':'.*'}
        self.save()

    def get_project_name():
        if "project" in self.config:
            return self.config['project']

    def save(self):
        fh = open(self.config_file,"w")
        fh.write(compile_json(self.config, indent=4))
        fh.close()

    def get_full_path(self, relpath):
        if relpath[0] == "/":
            return os.path.join(self.root, relpath[1:])
        else:
            return os.path.join(self.root, relpath)

    def push(self, url):
        hostname, project = parse_tx_url(url)
        url_resources = "%s/api/project/%s/resources" % (hostname, project)
        fh = urllib2.urlopen(url_resources)
        raw = fh.read()
        fh.close()
        remote_resources = parse_json(raw)

        local_resources = self.config['resources'].keys()
        for remote_resource in remote_resources:
            slug = remote_resource['slug']
            if slug in local_resources:
                local_resources.remove(slug)

        if not "-f" in sys.argv[1:] and local_resources != []:
            print "Following resources are not available on remote machine:", ", ".join(local_resources)
            print "Use -f to force creation of new resources"
            exit(1)
        else:
            pass

        for resource, _resource in self.config['resources'].iteritems():
            for lang, path in _resource['mapping'].iteritems():
                url_push = "/api/project/%s/resource/%s/" % (project, resource)
                filename = os.path.basename(path).encode("ascii") # WTF ascii?
                print "Pushing %s to %s" % (path, url_push)
                post_multipart("localhost:8000", url_push, [('target_language',lang.encode("ascii"))],[(filename, filename, open(self.get_full_path(path)).read())])

    def scan(self, url):

        hostname, project = parse_tx_url(url)
        from libtransifex.language import Languages
        Languages.pull(hostname)



        def match_resource(relpath):
            #if len(self.config['resources']) == 0:
                #raise ResourceError("No resources defined for current project")
            #if len(self.config['resources']) == 1:
                #for key, resource in self.config['resources'].iteritems():
                    #return key
            matched_resources = []
            total = 0
            for key, resource in self.config['resources'].iteritems():
                if not 'regex' in resource:
                    raise ResourceError("Multiple resources, but resource '%s' doesn't have 'regex' defined" % key)
                if re.match(resource['regex'], relpath):
                    matched_resources.append(key)
                    total += 1
            if total == 0:
                return None
            elif total == 1:
                return matched_resources[0]
            else:
                raise ResourceError("Ambiguous regular expressions, filename '%s' matched by regexes: %s" % (relpath, ",".join(matched_resources)))
      

        for resource in self.config['resources']:
            if 'mapping' in self.config['resources'][resource]:
                del self.config['resources'][resource]['mapping']

        print "Scanning in: %s" % self.root
        stringsets = []
        for root, dirs, files in os.walk(self.root):
            for filename in files:
              fullname = os.path.join(root, filename)
              for parser in parsers:
                    if not parser.accept(fullname):
                        continue
                    relpath = fullname[len(tx.root):]
                    resource = match_resource(relpath)
                    if not resource:
                        print "WARNING: File '%s' ignored" % relpath
                        continue
                    try:
                        stringset = parser.open(filename = relpath, root = tx.root)
                    except ParseError, err:
                        print "WARNING: Could not parse file '%s' (%s)" % (relpath, err)
                        continue

                    # If we could not get language code from file itself try extracting from
                    # path filter regex
                    if not stringset.target_language:
                        regex = self.config['resources'][resource]['regex']
                        if "<lang_code>" in regex:
                            stringset.target_language = re.match(regex, relpath).group('lang_code')

                    std_lang_code = Languages.lang_alias_to_code(stringset.target_language)
                    if not std_lang_code:
                        print "WARNING: Ignored file '%s' (Unknown language code %s)" % (relpath, stringset.target_language)
                        continue

                    stringset.target_language = std_lang_code
                    stringset.resource = resource
                    print "Parsed:", relpath
                    for j in stringsets:
                        if j.target_language == stringset.target_language and j.resource == stringset.resource:
                            raise ResourceError("Files %s and %s both match same language (%s) and same resource (%s)" % (j.filename, stringset.filename, stringset.target_language, stringset.resource))
                    stringsets.append(stringset)
                    if not 'mapping' in self.config['resources'][resource]:
                        self.config['resources'][resource]['mapping'] = {}
                    self.config['resources'][resource]['mapping'][stringset.target_language] = relpath
                    break
        self.save()
    
if len(sys.argv) <= 1:
    print HELP
    exit(1)

tx = Project()

cmd = sys.argv[1]
if cmd == "scan":
    tx.scan(sys.argv[2])

if cmd == "push":
    tx.push(sys.argv[2])