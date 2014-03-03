#!/bin/bash
# -*- coding: utf-8 -*-

# change to working dir
cd {{ working_dir }}
# run raxml
/Users/bcf/git/standard-RAxML/raxmlHPC-SSE3 -y -m {{ model }} -s {{ phylip }} -p {{ seed }} -n {{ starting_tree }}
