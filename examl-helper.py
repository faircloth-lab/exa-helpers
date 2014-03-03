#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
(c) 2014 Brant Faircloth || http://faircloth-lab.org/
All rights reserved.

This code is distributed under a 3-clause BSD license. Please see
LICENSE.txt for more information.

Created on 28 February 2014 09:37 PST (-0800)
"""

import os
import re
import random
import argparse
import subprocess

from phyluce.helpers import FullPaths, CreateDir, is_dir, is_file
from phyluce.log import setup_logging

import pdb

RAXML = "/Users/bcf/git/standard-RAxML/raxmlHPC-SSE3"
EXAML = "/Users/bcf/git/examl/examl/examl"
PARSER = "/Users/bcf/git/examl/parser/parser"

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
        "--model",
        choices = ["GTRGAMMA", "GTRCAT"],
        default="GTRGAMMA",
        help="""The substitution model to use."""
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=2,
        help="""The number of compute cores to use."""
    )
    parser.add_argument(
        "--trees",
        type=int,
        default=20,
        help="""The number of trees to search."""
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
    parser.add_argument(
        "--flag",
        action="store_true",
        default=False,
        help="""Help text""",
    )
    return parser.parse_args()


def convert_phylip_to_examl_binary(log, args):
    log.info("Converting PHYLIP to binary format")
    # make sure we're in output/working dir
    os.chdir(args.output)
    phylip_file_name = os.path.basename(args.phylip)
    binary_file_name = "{}.unpartitioned".format(phylip_file_name)
    binary_file_pth = os.path.join(args.output, binary_file_name)
    cmd = [
        PARSER,
        "-s",
        args.phylip,
        "-m",
        "DNA",
        "-n",
        binary_file_name
    ]
    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    try:
        stderr, stdout = proc.communicate()
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print stderr
    return "{}.binary".format(binary_file_pth)


def compute_starting_parsimony_tree(log, args, i, binary_file):
    log.info("[Tree {}] Computing parsimony starting tree".format(i))
    # make sure we're in output/working dir
    os.chdir(args.output)
    starting_tree = "{}.P{}.newick".format(
        os.path.basename(binary_file),
        i
    )
    starting_tree_pth = os.path.join(
        args.output,
        "RAxML_parsimonyTree.{}".format(starting_tree)
    )
    seed = random.randrange(0, 1000000)
    log.info("[Tree {}] Parsimony seed is {}".format(i, seed))
    # raxmlHPC-SSE3 -y -m GTRCAT -s dna.phy -p 12345 -n startingTree
    cmd = [
        RAXML,
        "-y",
        "-m",
        args.model,
        "-s",
        args.phylip,
        "-p",
        str(seed),
        "-n",
        starting_tree
    ]
    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    try:
        stderr, stdout = proc.communicate()
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print stderr
    return seed, starting_tree_pth


def run_examl_against_binary_data(log, args, i, binary_file_pth, starting_tree_pth):
    log.info("[Tree {}] Running examl using binary file and starting tree {}".format(
        i,
        os.path.basename(starting_tree_pth),
        ))
    # make sure we're in output/working dir
    os.chdir(args.output)
    ml_tree_name = "{}.T{}".format(
        os.path.basename(args.phylip),
        i
    )
    # determine correct model
    if args.model == "GTRCAT":
        model = "PSR"
    else:
        model = "GAMMA"
    # mpirun -np 8 examl -s 49.unpartitioned.binary -t 49.tree -m GAMMA -n T1
    cmd = [
        "mpirun",
        "-np",
        str(args.cores),
        EXAML,
        "-s",
        binary_file_pth,
        "-t",
        starting_tree_pth,
        "-m",
        model,
        "-n",
        ml_tree_name
    ]
    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    try:
        stderr, stdout = proc.communicate()
        ll_result = re.search("Likelihood\s+:\s(-\d+.\d+)", stderr)
        ll = ll_result.groups()[0]
        log.info("[Tree {}] LogLik {}".format(i, ll))
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print stderr


def main():
    args = get_args()
    # setup logging
    log, my_name = setup_logging(args)
    # change to working dir
    starting_dir = os.getcwd()
    # convert data to binary
    binary_file_pth = convert_phylip_to_examl_binary(log, args)
    for iter in xrange(args.trees):
        # compute starting tree on data
        seed, starting_tree_pth = compute_starting_parsimony_tree(log, args, iter, binary_file_pth)
        # run examl against binary data with starting tree
        run_examl_against_binary_data(log, args, iter, binary_file_pth, starting_tree_pth)
    # return to starting dir
    os.chdir(starting_dir)

if __name__ == '__main__':
    main()
