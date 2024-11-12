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

from requests import get
from requests.exceptions import HTTPError, RequestException, ReadTimeout, ConnectionError
from json.decoder import JSONDecodeError
from os.path import join
from threading import Thread, Condition
from time import sleep
from datetime import datetime, timedelta
import logging


class SDMLinks:
    def __init__(self, logger=None):
        self.official_list_data_models = ('https://raw.githubusercontent.com/smart-data-models/data-models/master/'
                                          'specs/AllSubjects/official_list_data_models.json')
        self.official_list_data_models_data = dict()

        self.data_models_metadata = 'https://smartdatamodels.org/extra/datamodels_metadata.json'
        self.data_models_metadata_data = dict()

        if logger is None:
            logging.basicConfig(filename='app.log',
                                filemode='w',
                                format='%(name)s - %(levelname)s - %(message)s',
                                level=logging.DEBUG)
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.check_interval_minutes = 720  # 12h * 60m
        self.obtained_time = datetime.now()

        # Create a Condition object
        self.data_available = Condition()

        # Start the background thread
        background_thread = Thread(target=self.get_files_background)
        background_thread.start()

    def get_files_background(self):
        while True:
            current_time = datetime.now()

            if len(self.data_models_metadata_data) == 0 or (current_time - self.obtained_time) > timedelta(days=7):
                self.official_list_data_models_data = self.__get_data__(url=self.official_list_data_models)
                self.data_models_metadata_data = self.__get_data__(url=self.data_models_metadata)

                self.obtained_time = datetime.now()

                self.logger.info("Download complete!")
                elapsed_time = self.obtained_time - current_time
                self.logger.info(f"Total time: {elapsed_time.total_seconds():.2f} seconds")

            with self.data_available:
                self.data_available.notify()

            # Sleep for the specified interval, in seconds
            sleep(self.check_interval_minutes * 60)

    @staticmethod
    def __get_data__(url: str) -> dict:
        response = None

        try:
            response = get(url=url, timeout=1)
            response.raise_for_status()
        except HTTPError as errh:
            print("HTTP Error")
            print(errh.args[0])
        except ConnectionError as conerr:
            print("Connection error")
            print(conerr)
        except RequestException as errex:
            print("Exception request")
            print(errex)
        except ReadTimeout as errrt:
            print("Time out")
            print(errrt)

        try:
            response = response.json()
        except JSONDecodeError as e:
            print("JSONDecodeError")
            print(e)

        return response

    def get_links(self, entity_name: str) -> dict:
        """
        Get the link to the repository and the link to the raw data of the model.yaml of the corresponding Data Model
        :param entity_name: The name of the entity to search the links in GitHub
        :return:
        """
        self.logger.info(f"Requesting links from entity '{entity_name}'")

        # Acquire the lock associated with the Condition
        with self.data_available:
            # Wait until data is available
            while self.official_list_data_models_data == dict():
                self.data_available.wait()

        data_model_metadata = \
            [x for x in self.data_models_metadata_data if x['dataModel'] == entity_name]

        official_data_model = \
            [x for x in self.official_list_data_models_data['officialList'] if entity_name in x['dataModels']]

        entity_repo_link = official_data_model[0]['repoLink']
        entity_repo_link = entity_repo_link.replace('.git', '')
        entity_repo_link = join(entity_repo_link, 'tree', 'master', entity_name)

        entity_yaml_link = data_model_metadata[0]['yamlUrl']

        response = {
            'entity_repo_link': entity_repo_link,
            'entity_yaml_link': entity_yaml_link
        }

        return response


if __name__ == '__main__':
    sdm_links = SDMLinks()
    repo_link, yaml_link = sdm_links.get_links(entity_name='WeatherObserved')

    print(f"Repository link: {repo_link}")
    print(f"Yaml link: {yaml_link}")
