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
from smartdatamodels.MD_exist import MDExist


class CheckExamples:
    def __init__(self, logger, data_model_repo_url, mail, json_output_filepath, generate_output_file=False):
        # FL stands for inside file check for one data model
        # this python file is focused on files under the examples folder
        # TODO: include geojson example in the future
        self.CHECK_EXAMPLES = ['example.json',
                               'example.jsonld',
                               'example-normalized.json',
                               'example-normalized.jsonld'
                               ]

        self.logger = logger
        self.data_model_repo_url = data_model_repo_url
        self.mail = mail
        self.json_output_filepath = json_output_filepath
        self.generate_output_file = generate_output_file

        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=generate_output_file)
        self.md_exist = MDExist(logger=logger, generate_output_file=generate_output_file)

    def check_fl_examples(self, tz, test_number) -> [bool, dict]:
        """
        Check files examples given the data model link
        """
        if self.generate_output_file:
            self.sdm_utils.send_message(test_number=test_number,
                                        mail=self.mail,
                                        tz=tz,
                                        check_type="loading")

        output = {"result": False}  # the json answering the test

        raw_schema_url = self.sdm_utils.get_schema_json_raw(self.data_model_repo_url)
        meta_schema = self.sdm_utils.open_jsonref(raw_schema_url)

        # go through all the files
        for checking_file in self.CHECK_EXAMPLES:

            raw_example_url = self.sdm_utils.create_example_url_raw(self.data_model_repo_url, checking_file)

            if self.generate_output_file:
                self.sdm_utils.send_message(test_number=test_number,
                                            mail=self.mail,
                                            tz=tz,
                                            check_type="processing",
                                            json_output=None,
                                            sub_test_name=f"{checking_file} check")

            # from normalized to key-value
            # validate the examples and schema.json
            cf_output = {"result": False}

            # check the parameters
            # 1. whether example file is readable
            # 2. whether example payload is valid with schema, additional properties is not allowed
            # 3. whether properties are duplicated defined
            result = self.sdm_utils.check_parameters(output=cf_output,
                                                     tz=tz,
                                                     json_output_filepath=self.json_output_filepath,
                                                     schema_url=raw_example_url,
                                                     mail=self.mail,
                                                     test=test_number,
                                                     meta_schema=meta_schema,
                                                     tag=checking_file)

            # if result is false, then there exists mentioned errors
            if not result:
                return result, cf_output

            # if result is true, return
            # cf_output: the json output dictionary
            # example_dict: the example dictionary
            cf_output, example_dict, _ = result
            cf_output["result"] = True

            # check the metadata of examples
            if checking_file.endswith("ld"):
                # check id, type, @context
                cf_output = self.md_exist.is_metadata_existed_examples(cf_output,
                                                                       example_dict,
                                                                       self.data_model_repo_url,
                                                                       checklist=["id", "type", "@context"])
            else:
                # check id, type
                cf_output = self.md_exist.is_metadata_existed_examples(cf_output,
                                                                       example_dict,
                                                                       self.data_model_repo_url,
                                                                       checklist=["id", "type"])

            output[checking_file] = cf_output

            if cf_output["metadata"]:
                # if metadata is not empty, then the test is failed, return the failed message
                output["cause"] = self.sdm_utils.message_after_check_example(cf_output)
                self.sdm_utils.customized_json_dumps(output=output,
                                                     tz=tz,
                                                     test_number=test_number,
                                                     json_output_filepath=self.json_output_filepath,
                                                     mail=self.mail,
                                                     flag=False)

                output.pop('jsonUrl')
                return False, output

        try:
            # generate examples referral for example-normalized.json and example-normalized.jsonld
            self.sdm_utils.generate_examples(
                self.sdm_utils.create_example_url_raw(self.data_model_repo_url, 'example-normalized.json'),
                self.sdm_utils.create_example_url_raw(self.data_model_repo_url, 'example-normalized.jsonld'),
                output, tz, test_number, self.json_output_filepath, self.mail)
        except Exception as e:
            print(e)
            print("Error when generating examples")

        self.sdm_utils.customized_json_dumps(output=output,
                                             tz=tz,
                                             test_number=test_number,
                                             json_output_filepath=self.json_output_filepath,
                                             mail=self.mail)

        output['message'] = "Test successfully executed"
        output.pop('jsonUrl')
        return True, output
