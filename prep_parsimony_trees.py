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
        action=CreateDir,
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


def compute_starting_parsimony_tree(log, args, env, i):
    log.info("[Parsimony Tree %s] Creating parsimony starting tree submit script" % i)
    # make sure we're in output/working dir
    starting_tree = "%s.P%s.newick" % (
        os.path.basename(args.phylip),
        i
    )
    submit_script = "raxml.parsimony.%s.P%s.sh" % (
        os.path.basename(args.phylip),
        i
    )
    submit_script_pth = os.path.join(args.output, submit_script)
    #starting_tree_pth = os.path.join(
    #    args.output,
    #    "RAxML_parsimonyTree.{}".format(starting_tree)
    #)
    seed = random.randrange(0, 1000000)
    log.info("[Parsimony Tree %s] Seed is %s" % (i, seed))
    # raxmlHPC-SSE3 -y -m GTRCAT -s dna.phy -p 12345 -n startingTree
    # write the submit script
    template = env.get_template('prep-parsimony.sh')
    if args.model == "PSR":
        model = "GTRCAT"
    else:
        model = "GTRGAMMA"
    formatted_result = template.render(
        working_dir=args.output,
        threads=args.threads,
        model=model,
        phylip=args.phylip,
        seed=seed,
        starting_tree=starting_tree
    )
    log.info("[Parsimony Tree %s] Writing submit script %s" % (i, submit_script))
    outf = open(submit_script_pth, 'w')
    outf.write(formatted_result)
    outf.close()
    return submit_script_pth


def submit_parsimony_job(log, args, env, i, submit_script_pth):
    log.info("[Parsimony Tree %s] Setting up queueing command" % i)
    template = env.get_template('prep-parsimony.submit')
    command_string = template.render(
        threads=args.threads,
        submit_script=submit_script_pth
    )
    qsub = shlex.split(command_string)
    log.info("[Parsimony Tree %s] Submitting job" % i)
    stderr, stdout = subprocess.Popen(
            qsub,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        ).communicate()
    log.info("[Parsimony Tree %s] Queing info %s | %s" % (i, stdout.strip(), stderr.strip()))


def prep_parser_script(log, args, env):
    log.info("[Binary phylip] Creating parser submit script")
    submit_script = "%s.examl-parser.sh" % (
        os.path.basename(args.phylip)
    )
    submit_script_pth = os.path.join(args.output, submit_script)
    template = env.get_template('prep-binary.sh')
    # the parser will add an extesion to the file after prepping the binary
    formatted_result = template.render(
        working_dir=args.output,
        phylip=args.phylip,
        binary_phylip=os.path.basename(args.phylip)
    )
    log.info("[Binary phylip] Writing submit script %s" % (submit_script))
    outf = open(submit_script_pth, 'w')
    outf.write(formatted_result)
    outf.close()
    return submit_script_pth


def submit_parser_job(log, args, env, submit_script_pth):
    log.info("[Binary phylip] Setting up queueing command")
    template = env.get_template('prep-binary.submit')
    command_string = template.render(
        submit_script=submit_script_pth
    )
    qsub = shlex.split(command_string)
    log.info("[Binary phylip] Submitting job")
    stderr, stdout = subprocess.Popen(
            qsub,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        ).communicate()
    log.info("[Binary phylip] Queing info %s | %s" % (stdout.strip(), stderr.strip()))


def main():
    args = get_args()
    # setup logging
    log, my_name = setup_logging(args)
    env = Environment(loader=FileSystemLoader(args.templates))
    for i in xrange(args.trees):
        submit_script_pth = compute_starting_parsimony_tree(log, args, env, i)
        submit_parsimony_job(log, args, env, i, submit_script_pth)
    # convert the phylip file to binary format
    submit_script_pth = prep_parser_script(log, args, env)
    submit_parser_job(log, args, env, submit_script_pth)
    text = " Completed {} ".format(my_name)
    log.info(text.center(65, "="))

if __name__ == '__main__':
    main()
