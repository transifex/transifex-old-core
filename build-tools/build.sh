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

echo "Cleaning up"

for dir in BUILD BUILDROOT RPMS SOURCES SPECS SRPMS; do
	rm -rf $dir/*
done

pushd transifex-core
./build.sh $1
popd
for file in `find /var/tmp/rpmbuild/ -name 'transifex*rpm'`; do cp $file . ; done

pushd transifex-extras
./build.sh $1
popd
for file in `find /var/tmp/rpmbuild/ -name 'transifex*rpm'`; do cp $file . ; done
