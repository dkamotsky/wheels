#!/usr/bin/env bash

# keyring set https://upload.pypi.org/legacy/ dkamotsky
# vi ~/.pypirc

rm -rf build dists
python setup.py dists
twine upload -r pypi dist/dkamotsky.logr-*
