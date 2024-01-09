#!/bin/bash

ln -s $(which python3) /usr/local/bin/python

python eml_to_html.py updates  ../../../Downloads/Update/*/*.eml