#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
(c) 2014 Brant Faircloth || http://faircloth-lab.org/
All rights reserved.

This code is distributed under a 3-clause BSD license. Please see
LICENSE.txt for more information.

Created on 02 March 2014 15:20 PST (-0800)
"""

import os
import glob
import shlex
import random
import argparse
import subprocess

from jinja2 import Environment, FileSystemLoader

from phyluce.helpers import FullPaths, CreateDir, is_dir, is_file
from phyluce.log import setup_logging

import pdb

def get_args():
    """Get arguments from CLI"""
    parser = argparse.ArgumentParser(
        description="""Run standard tree inference using raxml-light/examl"""
    )
    parser.add_argument(
        "--phylip",
        required=True,
        type=is_file,
        action=FullPaths,
        help="""The phylip file you want to run raxml against."""
    )
    parser.add_argument(
        "--output",
        required=True,
        action=FullPaths,
        help="""The output directory in which to store results."""
    )
    parser.add_argument(
        "--templates",
        required=True,
        action=FullPaths,
        type=is_dir,
        help="""The path to the queue submission templates."""
    )
    parser.add_argument(
        "--trees",
        required=True,
        type=int,
        default=20,
        help="""The number of trees to search."""
    )
    parser.add_argument(
        "--nodes",
        required=True,
        type=int,
        default=1,
        help="""The number of compute nodes to use."""
    )
    parser.add_argument(
        "--model",
        choices = ["GAMMA", "PSR"],
        default="GAMMA",
        help="""The substitution model to use."""
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        help="""The number of compute threads to use."""
    )
    parser.add_argument(
        "--verbosity",
        type=str,
        choices=["INFO", "WARN", "CRITICAL"],
        default="INFO",
        help="""The logging level to use."""
    )
    parser.add_argument(
        "--log-path",
        action=FullPaths,
        type=is_dir,
        default=None,
        help="""The path to a directory to hold logs."""
    )
    return parser.parse_args()


def get_starting_trees(log, args):
    log.info("[examl] Checking for parsimony trees")
    phyl = os.path.basename(args.phylip)
    # create a list of the format of tree names we expect
    expected = set(["RAxML_parsimonyTree.%s.P%s.newick" % (phyl, i) for i in xrange(args.trees)])
    # use glob to pull up a list of tree names in the expected directory
    observed = set([os.path.basename(i) for i in glob.glob(os.path.join(args.output, "RAxML_parsimonyTree.{}.P*.newick".format(phyl)))])
    # ensure those match
    try:
        assert expected == observed
    except:
        raise IOError('Parsimony trees appear missing or not in same number as expected')
    # return tree names
    return observed


def check_for_binary_phylip(log, args):
    log.info("[examl] Checking for binary alignment file")
    binary_name = "%s.binary" % os.path.basename(args.phylip)
    try:
        assert os.path.exists(os.path.join(args.output, binary_name))
    except:
        raise IOError('Binary phylip file appears to be missing')
    return binary_name


def prep_examl_script(log, args, env, starting_tree, binary_name):
    log.info("[examl] Creating examl submit script")
    # get the starting tree number
    treenum = starting_tree.split(".")[-2].replace("P", "")
    #
    submit_script = "%s.T%s.examl-submit.sh" % (
        os.path.basename(args.phylip),
        treenum
    )
    submit_script_pth = os.path.join(args.output, submit_script)
    template = env.get_template('examl.sh')
    # the parser will add an extension to the file after prepping the binary
    formatted_result = template.render(
        working_dir=args.output,
        nodes=args.nodes,
        binary_phylip=binary_name,
        starting_tree=starting_tree,
        model=args.model,
        ending_tree="T%s" % treenum
    )
    log.info("[examl] Writing submit script %s" % (submit_script))
    outf = open(submit_script_pth, 'w')
    outf.write(formatted_result)
    outf.close()
    return submit_script_pth


def main():
    args = get_args()
    # setup logging
    log, my_name = setup_logging(args)
    env = Environment(loader=FileSystemLoader(args.templates))
    # check for the binary aligment
    binary_name = check_for_binary_phylip(log, args)
    # check for starting trees
    starting_trees = get_starting_trees(log, args)
    # create the binary file
    for starting_tree in starting_trees:
        prep_examl_script(log, args, env, starting_tree, binary_name)
    text = " Completed {} ".format(my_name)
    log.info(text.center(65, "="))

if __name__ == '__main__':
    main()
