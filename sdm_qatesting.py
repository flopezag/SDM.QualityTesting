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

from cli.command import parse_cli
from api.server import launch, sdm_links
from common.config import CONFIG_DATA
from smartdatamodels.master_tests import SDMQualityTesting
from api.custom_logging import CustomizeLogger
from common.utils import extract_json_data
from sys import exit


def create_logger():
    customize_logger = CustomizeLogger.make_logger(config_data=CONFIG_DATA)

    return customize_logger


if __name__ == "__main__":
    args = parse_cli()

    if args["run"] is True:
        file_in = args["--input"]
        generate_files = args["--output"]
        logger = create_logger()

        data_model, email, tests = extract_json_data(filename=file_in, logger=logger)
        
        sdm_quality_testing = SDMQualityTesting(data_model_repo_url=data_model,
                                                mail=email,
                                                last_test_number=tests,
                                                logger=logger)
    
        resp = sdm_quality_testing.do_tests()
        sdm_quality_testing.stop()
        sdm_links.stop()

        print(resp)
        exit()

    elif args["server"] is True:
        port = int(args["--port"])
        host = args["--host"]

        launch(app="api.server:application", host=host, port=port)
