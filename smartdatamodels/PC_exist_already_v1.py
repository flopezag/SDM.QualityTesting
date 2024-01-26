# Check whether the properties are existent in the database already

# TODO: import the function from python package by "from pysmartdatamodel.utils import *"

from pymongo import MongoClient
from os.path import exists, getmtime, join
from zipfile import ZipFile
from datetime import datetime, timedelta
from threading import Thread
from time import sleep, time
from requests import get
from common.config import CODE_HOME


class SDMProperties:
    def __init__(self, logger):
        self.properties = dict()
        self.logger = logger

        file_url = "https://smartdatamodels.org/extra/smartdatamodels.zip"
        save_path = join(CODE_HOME, "mastercheck_output", "smartdatamodels.json")
        check_interval_minutes = 30

        # Start the background thread
        background_thread = Thread(target=self.check_file_background,
                                   args=(file_url, save_path, check_interval_minutes))

        background_thread.start()

    def check_file_background(self, url, file_path, interval_minutes):
        while True:
            if exists(file_path):
                modified_time = datetime.fromtimestamp(getmtime(file_path))
                current_time = datetime.now()
                if (current_time - modified_time) < timedelta(hours=1):
                    self.logger.info("File already exists and is less than 1 hour old. Skipping download.")
                else:
                    self.logger.info("File exists but is older than 1 hour. Downloading...")
                    self.download_file(url, file_path)
            else:
                self.logger.info("File does not exist. Downloading...")
                self.download_file(url, file_path)

            # Sleep for the specified interval
            sleep(interval_minutes * 60)

    def download_file(self, url, file_path):
        response = get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # Adjust the block size as per your needs

        start_time = time()  # Start time

        with open(file_path, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)
                downloaded_size = file.tell()
                progress = f"{downloaded_size}/{total_size} bytes downloaded"
                self.logger.info(progress)
                print(progress, end='\r', flush=True)

        end_time = time()  # End time

        self.logger.info("Download complete!")
        elapsed_time = end_time - start_time
        self.logger.info(f"Total time: {elapsed_time:.2f} seconds")

        with ZipFile('spam.zip') as myzip:
            with myzip.open('spam.txt') as my_file:
                self.properties = my_file.read()

    def is_property_already_existed(self, output, yamlDict):
        try:
            mongoDb = "smartdatamodels"
            mongoCollection = "properties"
            client = MongoClient()
            db = client[mongoDb]
            collProperties = db[mongoCollection]
            commonProperties = ["id", "name", "description", "location", "seeAlso", "dateCreated", "dateModified",
                                "source", "alternateName", "dataProvider", "owner", "address", "areaServed", "type"]
            existing = "alreadyUsedProperties"
            available = "availableProperties"

            #print("llego a la funcion")
            output[existing] = []
            output[available] = []

            for key in yamlDict:
                if key in commonProperties:
                    continue
                #print(key)
                lowKey = key.lower()
                patternKey = "^" + lowKey + "$"
                queryKey = {"property": {"$regex": patternKey, "$options": "i"}}

                results = list(collProperties.find(queryKey))
                #print(len(results))
                if len(results) > 0:
                    definitions= []
                    dataModelsList = []
                    types = []
                    for index, item in enumerate(results):
                        dataModelsList.append(str(index + 1) + ".-" + item["dataModel"])
                        #print(item["type"])
                        if "description" in item or "type" in item:
                            if "description" in item:
                                definitions.append(str(index + 1) + ".-" + item["description"])
                            else:
                                definitions.append(str(index + 1) + ".- missing description")
                            if "type" in item:
                                types.append(str(index + 1) + ".-" + item["type"])
                            else:
                                types.append(str(index + 1) + ".- missing type")
                        else:
                            output[existing].append({"Error": lowKey})
                    output[existing].append({key: "Already used in data models: " + ",".join(dataModelsList)
                                                  + " with these definitions: " + chr(13).join(definitions)
                                                  + " and these data types: " + ",".join(types)})
                else:
                    output[available].append({key: "Available"})

        except Exception as e:
            print(e)
            output[existing].append({"Error": lowKey})

        return output



