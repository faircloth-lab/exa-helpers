#!/bin/bash
# -*- coding: utf-8 -*-

# change to working dir
cd {{ working_dir }}

# run the parser to create a binary file
/Users/bcf/git/examl/parser/parser -s {{ phylip }} -m DNA -n {{ binary_phylip }}
