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

from io import TextIOWrapper
from json import load, JSONDecodeError
from logging import RootLogger


def extract_json_data(filename: TextIOWrapper, logger: RootLogger) -> [str, str, int]:
    try:
        # Load the JSON content
        data = load(filename)

        # Check if the keys are exactly  "data_model", "email", and "tests"
        expected_keys = {'data_model', 'email', 'tests'}
        if set(data.keys()) != expected_keys:
            raise ValueError(f"JSON must contain exactly keys: {expected_keys}")

        # Validate data types
        if not isinstance(data['data_model'], str):
            raise ValueError("Key 'data_model' must be a string. Current value: {data['data_model']}")

        if not isinstance(data['email'], str):
            raise ValueError("Key 'email' must be a string. Current value: {data['email']}")

        if not isinstance(data['tests'], (int, float)):
            raise ValueError("Key 'tests' must be a number. Current value: {data['tests']}")

        logger.debug("JSON is valid and contains the correct structure.")

        return data['data_model'], data['email'], data['tests']

    except JSONDecodeError:
        print("Invalid JSON format.")

    except ValueError as ve:
        print(ve)
