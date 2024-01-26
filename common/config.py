#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##
# Copyright 2023 FIWARE Foundation, e.V.
#
# This file is part of SDM.QualityTesting
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
from pathlib import Path
from json import load
from os import environ
from os.path import dirname, join, abspath, exists
from jsonref import loads

__author__ = 'Fernando López'

__version__ = '1.2.0'

config_path = Path.cwd().joinpath('common/config.json')

with open(config_path) as config_file:
    config = load(config_file)

# Settings file is inside Basics directory, therefore I have to go back to the parent directory
# to have the Code Home directory
CODE_HOME = dirname(dirname(abspath(__file__)))
LOG_HOME = join(CODE_HOME, 'logs')

"""
Default configuration.

The configuration `cfg_defaults` are loaded from `cfg_filename`, if file exists in
/etc/fiware.d/sdm.quality-testing.json

Optionally, user can specify the file location manually using an Environment variable
called SDM_QUALITY_TESTING_FILE.
"""

name = 'sdm.quality-testing'

cfg_dir = "/etc/fiware.d"

cfg_filename = environ.get("SDM_QUALITY_TESTING_FILE")

if cfg_filename is None or exists(cfg_filename) is False:
    print("WARNING: Environment variable 'SDM_QUALITY_TESTING_FILE' is not defined.\n"
          "Trying to load '/etc/fiware.d/sdm.quality-testing.json' file")

    # 1st Alternative: The config file must be in /etc/fiware.d folder
    cfg_filename = join(cfg_dir, '%s.json' % name)
    if exists(cfg_filename) is False:
        # 2nd Alternative: The config file should be filled in the corresponding code folder
        cfg_filename = join(CODE_HOME, "common", "config.json")

        if exists(cfg_filename) is False:
            msg = '\nERROR: There is not defined SDM_QUALITY_TESTING_FILE environment variable ' \
                  '\n       pointing to configuration file or there is no config.json file' \
                  '\n       either in the /etd/init.d directory or ./common folder of the code.' \
                  '\n\n       Please correct at least one of them to execute the program.'
            exit(msg)

with open(cfg_filename, "r") as file:
    CONFIG_DATA = loads(file.read())
