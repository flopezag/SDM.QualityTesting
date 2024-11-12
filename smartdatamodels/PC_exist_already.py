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

# Check whether the properties are existent in the database already

# TODO: import the function from python package by "from pysmartdatamodel.utils import *"

from os.path import exists, getmtime, join
from gzip import open, GzipFile, decompress
from datetime import datetime, timedelta
from threading import Thread, Condition, Event
from time import sleep, time
from requests import get
from common.config import CODE_HOME
from json import loads


class SDMProperties:
    def __init__(self, logger):
        self.properties = list()
        self.logger = logger

        self.file_url = "https://smartdatamodels.org/extra/smartdatamodels.gz"
        self.gz_save_path = join(CODE_HOME, "mastercheck_output", "smartdatamodels.gz")
        self.json_save_path = join(CODE_HOME, "mastercheck_output", "smartdatamodels.json")

        self.check_interval_minutes = 1

        # Create a Condition object
        self.data_available = Condition()

        # Create a stop event
        self._kill = Event()

        # Start the background thread
        self.background_thread = Thread(target=self.check_file_background)
        self.background_thread.start()

    def check_file_background(self):
        while not self._kill.is_set():
            if exists(self.gz_save_path):
                modified_time = datetime.fromtimestamp(getmtime(self.gz_save_path))
                current_time = datetime.now()
                if (current_time - modified_time) < timedelta(hours=1):
                    self.logger.debug("File already exists and is less than 1 hour old. Skipping download.")
                    if not self.properties:
                        self.read_file()
                    else:
                        with self.data_available:
                            self.data_available.notify()
                else:
                    self.logger.debug("File exists but is older than 1 hour. Downloading...")
                    self.download_file()
                    self.read_file()
            else:
                self.logger.debug("File does not exist. Downloading...")
                self.download_file()
                self.read_file()

            # Sleep for the specified interval
            sleep(self.check_interval_minutes * 60)

    def download_file(self):
        response = get(self.file_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # Adjust the block size as per your needs

        start_time = time()  # Start time

        with open(self.gz_save_path, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)
                downloaded_size = file.tell()
                progress = f"{downloaded_size}/{total_size} bytes downloaded"
                # print(progress, end='\r', flush=True)
                self.logger.debug(progress)

        end_time = time()  # End time

        self.logger.info("Download complete!")
        elapsed_time = end_time - start_time
        self.logger.info(f"Total time: {elapsed_time:.2f} seconds")

    def read_file(self):
        with self.data_available:
            f = GzipFile(self.gz_save_path, "rb", )
            properties = f.read()
            decompressed_data = decompress(properties)
            json_data = loads(decompressed_data)

            keys_to_keep = ['property', 'dataModel', 'description', 'type']
            self.properties = [
                {key: d[key] for key in keys_to_keep if key in d}
                for d in json_data
            ]

            self.data_available.notify()

        self.logger.info("Database file read")

    def is_property_already_existed(self, output, yaml_dict):
        common_properties = ["id", "name", "description", "location", "seeAlso", "dateCreated", "dateModified",
                             "source", "alternateName", "dataProvider", "owner", "address", "areaServed", "type"]

        data_models_list = list()
        descriptions = list()
        types = list()
        output["alreadyUsedProperties"] = list()
        output["availableProperties"] = list()

        def get_value(data_property, property_key, error_message):
            try:
                return data_property[property_key]
            except KeyError:
                return error_message

        try:
            # Acquire the lock associated with the Condition
            with self.data_available:
                # Wait until data is available
                while len(self.properties) == 0:
                    self.data_available.wait()

            keys_yaml_data = list(yaml_dict.keys())
            keys_to_search = [key for key in keys_yaml_data if key not in common_properties]
            data_properties = [x for x in self.properties if x['property'] in keys_to_search]

            # TODO: Need to check if the attribute is not defined in the smart data models database
            for index, item in enumerate(keys_to_search):
                aux = [x for x in data_properties if x['property'] == item]

                if not aux:
                    output["availableProperties"].append({item: "Available"})
                    continue

                data_models_list.append([f"{index + 1}.- {x['dataModel']}" for x in aux])

                descriptions.append(
                    [f"{index + 1}.-{get_value(x, 'description', 'missing description')}"
                     for x in aux])

                # The descriptions may be different but we assume this issue for the moment
                # descriptions = [list(set(x)) for x in descriptions]
                # properties_problem_description = [x for x in descriptions if len(x) > 1]
                #
                # if len(properties_problem_description) > 0:
                #     output["alreadyUsedProperties"].append(
                #         {"Error": f"Same property '{item}' with different descriptions provided: "
                #                   f"{properties_problem_description}."})

                types.append(
                    [f"{index + 1}.-{get_value(x, 'type', 'missing type')}"
                     for x in aux])

                # The types MUST be the same, so we check that all the properties defined in SDM
                # have the same type
                types = [list(set(x)) for x in types]
                properties_problem_type = [x for x in types if len(x) > 1]

                if len(properties_problem_type) > 0:
                    output["alreadyUsedProperties"].append(
                        {"Error": f"Same property '{item}' with different types provided: "
                                  f"{properties_problem_type}."})

                # message = (f"Already used in data models: '{', '.join(data_models_list[index])}' "
                #           f"with these definitions: '{chr(13).join(descriptions[index])}' "
                #           f"and these data types: '{', '.join(types[index])}'")
                message = (f"Already used in data models: '{', '.join(data_models_list[0])}' "
                           f"with these definitions: '{chr(13).join(descriptions[0])}' "
                           f"and these data types: '{', '.join(types[0])}'")

                output["alreadyUsedProperties"].append({item: message})

        except Exception as e:
            print(e)
            output["alreadyUsedProperties"].append({"Error": "Unknown key"})

        return output

    def stop(self):
        """
        Send the message to stop the thread
        """

        # Signal the thread to stop
        self._kill.set()

        # Wait for the thread to finish
        self.background_thread.join()
        self.background_thread.join()

        self.logger.debug("Thread has been stopped.")
