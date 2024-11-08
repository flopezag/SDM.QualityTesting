#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##
# Copyright 2024 FIWARE Foundation, e.V.
#
# This file is part of SDM Quality Testing
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
##
"""SDM Quality Testing

Usage:
  sdm_qatesting.py run (--input FILE) [--output]
  sdm_qatesting.py server [--host HOST] [--port PORT]
  sdm_qatesting.py (-h | --help)
  sdm_qatesting.py --version

Arguments:
  FILE   input file
  PORT   http port used by the service

Options:
  -i, --input FILEIN  description to specify the file to the script
  -o, --output        generate the corresponding output file
  -h, --host HOST     launch the server in the corresponding host
                      [default: 127.0.0.1]
  -p, --port PORT     launch the server in the corresponding port
                      [default: 5600]

  -H, --help          show this help message and exit
  -v, --version       show version and exit

"""

from docopt import docopt
from os.path import basename
from sys import argv
from schema import Schema, And, Or, Use, SchemaError  # type: ignore


__version__ = "0.1.0"
__author__ = "fla"


def parse_cli() -> dict:
    if len(argv) == 1:
        argv.append("-h")

    version = f"SDM Quality Testing version {__version__}"

    args = docopt(__doc__.format(proc=basename(argv[0])), version=version)

    schema = Schema(
        {
            "--help": bool,
            "--input": Or(None, Use(open, error="--input FILE, FILE should be readable")),
            "--output": bool,
            "--port": Or(
                None,
                And(Use(int), lambda n: 1 < n < 65535),
                error="--port N, N should be integer 1 < N < 65535",
            ),
            "--host": Or(None, str, error="--host HOST should be a string"),
            "--version": bool,
            "run": bool,
            "server": bool,
        }
    )

    try:
        args = schema.validate(args)
    except SchemaError as e:
        exit(e)

    return args


if __name__ == "__main__":
    print(parse_cli())
