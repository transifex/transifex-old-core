#!/usr/bin/python
# Script to update components. Call as follows:
#
#  cd path/to/tx-django
#  python -m repowatch.update [<slugs of components to update>]
#
# If no slugs are given then all components with units will be updated

import operator
import itertools
import sys

from django.core.management import setup_environ
from django.contrib.sites.models import Site

import repowatch
from project.models import Collection
from models import Watch

def main(args):
    import settings
    setup_environ(settings)

    if len(args) > 1:
        comps = Component.objects.filter(slug__in=args[1:])
    else:
        comps = Component.objects.filter(unit__isnull=False)

    for comp in comps:
        comp.prepare_repo()
        watches = Watch.objects.filter(component=comp)
        repochanged = False
        changes = []
        for watch in watches:
            try:
                newrev = comp.get_rev(watch.path)
                if newrev != watch.rev:
                    if not watch.path:
                        repochanged = True
                    else:
                        changes.append((watch.user, watch.path))
            except ValueError:
                continue
        if changes:
            changes.sort(operator.itemgetter(0)
            for usergroup in itertool.groupby(changes,
                key=operator.itemgetter(0)):
                repowatch.send_email(Site.objects.get_current(), comp,
                    usergroup[0], repochanged,
                    [change[1] for change in usergroup[1]])

if __name__ == '__main__':
    main(sys.argv) 
