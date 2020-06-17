#!/bin/sh
# Install buildout script in virtual environment and run it.
# Call as: run_buildout.sh <module_path>/requirements-bootstrap.txt <buildout_dir>
echo "Start run of buildout"
set -e
echo "Parameters $1 $2"
REQUIREMENTS_FILE=$1
BUILDOUT_DIR=$2
cd $BUILDOUT_DIR
python3 -m venv  .
. bin/activate
echo "In virtual ennvironment"
pip3 install -r $REQUIREMENTS_FILE
echo "Requirements installed, about to run actual buildout"
# python bin/buildout -N -q
python bin/buildout -N
exit 0
