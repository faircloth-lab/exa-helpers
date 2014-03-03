#!/bin/bash
# -*- coding: utf-8 -*-

# change to working dir
cd {{ working_dir }}
# run raxml
/usr/local/raxml/latest/raxmlHPC-PTHREADS-SSE3 -T {{ threads }} -y -m {{ model }} -s {{ phylip }} -p {{ seed }} -n {{ starting_tree }}
