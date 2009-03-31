import os.path
import glob

conffiles = glob.glob(os.path.join(os.path.dirname(__file__), '*.conf'))

conffiles.sort()

for f in conffiles:
    execfile(f)
