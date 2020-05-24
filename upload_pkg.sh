#!/bin/bash

# install the following if not already done:

rm -rf ./build ./dist

virtualenv pkg_upload
source ./pkg_upload/bin/activate

#python3 -m pip install --user --upgrade setuptools wheel
python3 -m pip install --upgrade setuptools wheel

python3 setup.py sdist bdist_wheel

#python3 -m pip install --user --upgrade twine
python3 -m pip install --upgrade twine

echo "NOTE: enter '__token__' for the username on the next setp (hit Enter to continue)"
read s

python3 -m twine upload --repository pypi dist/*

#deactivate
