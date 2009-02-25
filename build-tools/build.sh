#!/bin/bash

which rpmbuild >& /dev/null
if [ ! "$?" = "0" ]; then
	echo "rpmbuild is not installed in your system; exiting"
	exit 1
fi

if [ ! "$#" = "1" ]; then
	echo "This script requires a single argument specifying the package version to build"
	echo "i.e. ./build.sh 1.2.3 for building version 1.2.3"
	exit 1
fi

export REPO='http://code.transifex.org/index.cgi/mainline'
export RPMBUILDROOT=`rpmbuild --showrc | grep _topdir | grep -v '{_topdir}' | awk '{print $3}'`

if [ "$RPMBUILDROOT" = "" ]; then
	echo "The RPM _topdir build directory does not seem to be specified; please make sure it's set"
	echo "For instance you can add '%_topdir      /var/tmp/rpmbuild' in ~/.rpmmacros"
	exit 1
fi

echo "Cleaning up"

pushd transifex-core
./build.sh $1
popd
for file in `find $RPMBUILDROOT -name 'transifex*rpm'`; do cp $file . ; done

pushd transifex-extras
./build.sh $1
popd
for file in `find $RPMBUILDROOT -name 'transifex*rpm'`; do cp $file . ; done
