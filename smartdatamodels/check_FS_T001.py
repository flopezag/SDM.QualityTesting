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

# Stands for check physical structure of one data model
# which is to check: 
#       - File exists
#       - File type correct
#       - Name correctly
# 
#  Least acceptable (LA) data model structure is as follows:
#   /
#       - examples/
#           - example-normalized.json or example-normalized.jsonId
#       - schema.json
# 
#  Other cases: general acceptable data model, and complete data model structure (CM)

from datetime import datetime
from smartdatamodels.utils import SDMUtils


class CheckStructure:
    def __init__(self, logger, data_model_repo_url, mail, json_output_filepath, generate_output_file=False):
        self.logger = logger
        self.data_model_repo_url = data_model_repo_url
        self.mail = mail
        self.json_output_filepath = json_output_filepath
        self.generate_output_file = generate_output_file

        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=generate_output_file)

    # url: check whether return 200
    def check_fs_minimal(self, tz, test_number) -> [bool, dict]:
        """
        Check the file structure to meet the minimal requirements
            - examples/
                - example-normalized.json or example-normalized.jsonld
            - schema.json
        """

        output = {"result": False}  # the json answering the test

        examples = (
            self.sdm_utils.is_url_existed(self.data_model_repo_url + "/examples"))[0]

        schema_json = (
            self.sdm_utils.is_url_existed(self.data_model_repo_url + "/schema.json"))[0]

        normalized_json = (
            self.sdm_utils.is_url_existed(self.data_model_repo_url + "/examples/example-normalized.json"))[0]

        normalized_jsonld = (
            self.sdm_utils.is_url_existed(self.data_model_repo_url + "/examples/example-normalized.jsonld"))[0]

        if not examples:
            output["cause"] = (f"{self.data_model_repo_url.split('/')[-1]} "
                               f"Missing examples folder: Cannot open the url at "
                               f"{self.data_model_repo_url}/examples")

            output["time"] = str(datetime.now(tz=tz))
            self.sdm_utils.customized_json_dumps(output=output,
                                                 tz=tz,
                                                 test_number=test_number,
                                                 json_output_filepath=self.json_output_filepath,
                                                 mail=self.mail,
                                                 flag=False)

            output.pop('jsonUrl')
            return False, output

        if not schema_json:
            output["cause"] = (f"{self.data_model_repo_url.split('/')[-1]} Missing schema.json: Cannot open the url at "
                               f"{self.data_model_repo_url}/schema.json")

            output["time"] = str(datetime.now(tz=tz))
            self.sdm_utils.customized_json_dumps(output=output,
                                                 tz=tz,
                                                 test_number=test_number,
                                                 json_output_filepath=self.json_output_filepath,
                                                 mail=self.mail,
                                                 flag=False)

            output.pop('jsonUrl')
            return False, output

        if not (normalized_json | normalized_jsonld):
            output["cause"] = (f"{self.data_model_repo_url.split('/')[-1]} "
                               f"Missing example-normalized.json or example-normalized.jsonld: at least one is a must")

            output["time"] = str(datetime.now(tz=tz))
            self.sdm_utils.customized_json_dumps(output=output,
                                                 tz=tz,
                                                 test_number=test_number,
                                                 json_output_filepath=self.json_output_filepath,
                                                 mail=self.mail,
                                                 flag=False)

            output.pop('jsonUrl')
            return False, output

        self.sdm_utils.customized_json_dumps(output=output,
                                             tz=tz,
                                             test_number=test_number,
                                             json_output_filepath=self.json_output_filepath,
                                             mail=self.mail)

        output['message'] = "Test successfully executed"
        output.pop('jsonUrl')
        return True, output

    def check_fs_normal(self, tz, test_number):
        """
        Check the file structure to meet the normal requirements
            - examples/
                - example.json
                - example.jsonld
                - example-normalized.json
                - example-normalized.jsonld
            - schema.json
        """
        pass

    def check_fs_full(self, tz, test_number):
        """
        Check the file structure to meet the full requirements
            - examples/
                - example.json
                - example.jsonld
                - example-normalized.json
                - example-normalized.jsonld
            - schema.json
            - ADOPTERS.yaml
            - notes.yaml
        """
        pass

    def check_file_structure(self, tz, test_number, check_type="minimal"):
        """
        Check the file structure
        """
        if self.generate_output_file:
            self.sdm_utils.send_message(test_number, self.mail, tz, check_type="loading")

        if check_type == "minimal":
            #     def check_fs_minimal(self, tz, test_number):
            return self.check_fs_minimal(tz=tz, test_number=test_number)
        elif check_type == "normal":
            return self.check_fs_normal(tz=tz, test_number=test_number)
        elif check_type == "full":
            return self.check_fs_full(tz=tz, test_number=test_number)
