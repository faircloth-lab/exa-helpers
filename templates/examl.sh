#!/bin/bash
# -*- coding: utf-8 -*-

# change to working dir
cd {{ working_dir }}

# setup examl run
/usr/local/mpich2/1.4.1p1/gcc_4.5.3/bin/mpirun \
    -n {{ nodes }} \
    /usr/local/examl/latest/bin/examl \
    -s {{ binary_phylip }} \
    -t {{ starting_tree }} \
    -m {{ model }} \
    -n {{ ending_tree }}

# delete checkpointed files
rm -f ExaML_binaryCheckpoint.{{ ending_tree }}_*
