#!/bin/bash
# -*- coding: utf-8 -*-

# change to working dir
cd {{ working_dir }}

# run the parser to create a binary file
/usr/local/examl/latest/bin/parser -s {{ phylip }} -m DNA -n {{ binary_phylip }}
