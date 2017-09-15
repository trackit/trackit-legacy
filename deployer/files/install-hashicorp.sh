#!/bin/sh

set -e

wget \
	--no-verbose \
	--input-file=urls \
	--no-clobber
sha256sum -c shasums
chmod +x nomad consul terraform
mv nomad consul terraform /usr/bin
