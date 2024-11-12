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

# Check whether the metadata is properly reported in schema.json

from validator_collection import checkers
from smartdatamodels.utils import SDMUtils
# TODO: import the function from python package by "from pysmartdatamodel.utils import *"


class MDReported:
    def __init__(self, logger, generate_output_file):
        self.logger = logger
        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=generate_output_file)

    def is_metadata_properly_reported(self, output, schema_dict):
        try:
            metadata = "metadata"
            output[metadata] = {}
            if "derivedFrom" in schema_dict:
                derived_from = schema_dict["derivedFrom"]
                if derived_from != "":
                    # check that it is a valid url
                    if not checkers.is_url(derived_from):
                        output["metadata"]["derivedFrom"] = {"warning": "derivedFrom is not a valid url"}
                    else:
                        if not self.sdm_utils.is_url_existed(derived_from)[0]:
                            output["metadata"]["derivedFrom"] = {"warning": "derivedFrom url is not reachable"}
            else:
                output["metadata"]["derivedFrom"] = \
                    {"warning": "not derivedFrom clause, include derived_from = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["derivedFrom"] = \
                {"warning": "not possible to check derivedFrom clause, "
                            "Does it exist a derivedFrom = '' clause in the header?"}

        # check that the header license is properly reported
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "license" in schema_dict:
                data_model_license = schema_dict["license"]
                if data_model_license != "":
                    # check that it is a valid url
                    if not checkers.is_url(data_model_license):
                        output["metadata"]["license"] = \
                            {"warning": "License is not a valid url. It should be a link to the license document"}
                    else:
                        if not self.sdm_utils.is_url_existed(data_model_license)[0]:
                            output["metadata"]["license"] = \
                                {"warning": "license url is not reachable"}
                else:
                    output["metadata"]["license"] = \
                        {"warning": "license is empty, include a license = '' in the header "}
            else:
                output["metadata"]["license"] = \
                    {"warning": "not license clause, does it exist a license = '' in the header?"}
        except Exception as e:
            print(e)
            output["metadata"]["license"] = \
                {"warning": "not possible to check license clause"}

        return output
