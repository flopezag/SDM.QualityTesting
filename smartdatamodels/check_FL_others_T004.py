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

from smartdatamodels.utils import SDMUtils


# FL stands for inside file check for one data model
# this python file is focused on other files
# like notes.yaml, ADOPTERS.yaml, CONTRIBUTORS.yaml, LICENSE.md
class CheckOtherFiles:
    def __init__(self, logger, data_model_repo_url, mail, json_output_filepath, generate_output_file=False):
        self.CHECK_OTHERS = [
            "notes.yaml",
            "ADOPTERS.yaml",
        ]

        self.logger = logger
        self.data_model_repo_url = data_model_repo_url
        self.mail = mail
        self.json_output_filepath = json_output_filepath
        self.generate_output_file = generate_output_file

        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=generate_output_file)

    def check_fl_others(self, tz, test_number) -> [bool, dict]:
        """
        Check other files given the data model link
        """

        if self.generate_output_file:
            self.sdm_utils.send_message(test_number, self.mail, tz, check_type="loading")

        output = {"result": False}  # the json answering the test

        # go through all the files
        for checking_file in self.CHECK_OTHERS:
            file_url = self.sdm_utils.get_other_files_raw(self.data_model_repo_url, checking_file)

            # check whether yaml file is valid
            cf_output = dict()
            result, output, _ = self.sdm_utils.is_valid_yaml(output=cf_output,
                                                             tz=tz,
                                                             json_output_filepath=self.json_output_filepath,
                                                             yaml_url=file_url,
                                                             mail=self.mail,
                                                             test=test_number,
                                                             tag="yamls")

            if not result:
                return result, output

            # cf_output, yaml_dict = result

            if self.generate_output_file:
                self.sdm_utils.send_message(test_number=test_number,
                                            mail=self.mail,
                                            tz=tz,
                                            check_type="processing",
                                            json_output=None,
                                            sub_test_name=f"{checking_file} check")

            # TODO: check there's an email in the ADOPTERS.yaml file

        output = self.sdm_utils.customized_json_dumps(output=output,
                                                      tz=tz,
                                                      test_number=test_number,
                                                      json_output_filepath=self.json_output_filepath,
                                                      mail=self.mail)

        output['message'] = "Test successfully executed"
        output.pop('jsonUrl')
        return True, output
