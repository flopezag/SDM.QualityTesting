from json import load, dump, loads, JSONDecodeError
from jsonref import loads as jsonref_loads
from re import sub, match
from requests import get
from datetime import datetime, timezone, time
from yaml import safe_load
from common.config import CONFIG_DATA
from validator_collection import checkers
from jsonschema import validate, SchemaError, Draft202012Validator
from jsonschema.exceptions import ValidationError


class SDMUtils:
    def __init__(self, logger, generate_output_file: bool = False):
        self.logger = logger
        self.generate_output_file = generate_output_file

        self.propertyTypes = ["Property", "Relationship", "GeoProperty"]

        self.TESTS = [
            "File Structure Check",
            "schema.json Content Check",
            "examples Check",
            "Others files Check"]

        self.KEYWORDS_FOR_CERTAIN_CHECK = "smart-data-models"

        self.CHECKED_PROPERTY_CASES = ['well documented', 'already used', 'newly available', 'Metadata', 'Failed']

        self.SUFFIX = "mastercheck"

        self.schema_json_yaml_dict = dict()

        self.example_v2_output_filepath = None
        self.exampleLDOutput_filepath = None

        ################################################
        # Frontend message formats and functions related to message
        #
        # Simple message formats are:
        #   - starting, ending, under processing, loading, passed, failed, previous tests message...
        #
        # Complex message formats are schema related, in order to give more concise info for contirbutors
        ################################################

        self.newline = "\n"
        # newsub_line = "\n   "

    @staticmethod
    def mf_test_start(json_output):
        return f"Subject: {json_output['subject']} Data Model: {json_output['data_model']} CHECK starts ... \n"

    @staticmethod
    def mf_test_end(message):
        return (f"{message} \n"
                f"Please be reminded that the JSON output file will be temporarily stored FOR one hour. \n "
                f"{''.join(['#'] * 30)}\n")

    def mf_test_basic(self, test_number, tz):
        return f"{self.get_now_verbose(tz)} Test {test_number} {self.TESTS[test_number - 1]}"

    def mf_test_processing(self, sub_test_name, tz):
        return f"{self.get_now_verbose(tz)} \t {sub_test_name} is processing ... \n"

    def mf_test_loading(self, test_number, tz):
        return self.mf_test_basic(test_number, tz) + " loading ...\n"

    def mf_test_passed(self, test_number, tz, message):
        return self.mf_test_basic(test_number, tz) + " passed!\n" + message + "\n"

    def mf_test_failed(self, test_number, tz, message):
        return self.mf_test_basic(test_number, tz) + " failed!\n\n" + message + "\n"

    def mf_test_previous(self, test_number):
        return f"Previous Checked Tests - Test {test_number} {self.TESTS[test_number - 1]}: "

    def mf_test_json(self, json_output, test_number):
        return (f"<a href='{self.get_json_output_url(json_output, test_number)}'>"
                f"Please find the JSON data file for more detail.</a>\n\n")

    def mf_test_example_normalized(self, example_v2_output):
        return (f"Systematically generated "
                f"<a href='{self.get_normalized_examples_url(example_v2_output)}'>example-normalized.json</a> "
                f"and <a href='{self.get_normalized_examples_url(example_v2_output)}'>example-normalized.json</a> \n\n")

    @staticmethod
    def write_msg_to_file(message, mail):
        """
        Write message into the output file, which will display on the website

        Parameters:
            message (str): the return message
            mail (str): the mail of the user, used it to get the output file in
        """
        # Just for the moment
        json_output_dir = "./mastercheck_output/"
        with open(json_output_dir + f"test_output_{mail}.txt", "a", newline="\n") as f:
            f.write(message)

    def send_message(self, test_number, mail, tz, check_type, json_output=None, sub_test_name=""):
        """
        Create the message given different tests, types, and sub_test_name

        Parameters:
            test_number (int): the number of test, 1 - file structure check, 2 - schema.json check,
                            3 - examples check, 4 - other files check
            mail (str): the mail of the user
            tz : timezone
            check_type (str): the types of check processing, including: "start", "loading", "passed", "processing",
                        "failed", "previous"
            json_output [None|dict]: the output dictionary for all tests
            sub_test_name (str): the name of the sub_test. In schema.json check, it includes property check and metadata check;
                                In examples check, it contains the checks for four types of example files

        """
        message = ""

        if not json_output:
            json_output = dict()

        if check_type == "loading":  # the return message when loading the check
            message = self.mf_test_loading(test_number, tz)

        elif check_type == "passed":  # the return message when the check passed

            # global example_v2_output_filepath, exampleLDOutput_filepath
            message = self.mf_test_passed(test_number, tz, json_output[test_number]["message"])

            # generate the referral examples for examples-normalized.json and examples-normalized.jsonld files
            # if the examples check passed
            if self.example_v2_output_filepath is not None and self.exampleLDOutput_filepath is not None:
                message += (self.mf_test_example_normalized(self.example_v2_output_filepath))

                self.example_v2_output_filepath, self.exampleLDOutput_filepath = None, None

            # generate the message contains the link to json output dictionary
            message += self.mf_test_json(json_output, test_number)

        elif check_type == "processing":  # the return message when processing sub-tests
            message = self.mf_test_processing(sub_test_name, tz)

        elif check_type == "failed":  # the return message when check failed

            if test_number == 2:
                # 2 - schema.json check
                message = self.mf_test_failed(test_number, tz, json_output[test_number]["message"])
            else:
                # 3 - examples check
                message = self.mf_test_failed(test_number, tz, json_output[test_number]["cause"])

            message = f"{message}\n{self.mf_test_json(json_output, test_number)}"

        elif check_type == "start":  # the return message when check starts
            message = self.mf_test_start(json_output)

        elif check_type == "previous":
            # the return message if the check has been done within one hour
            # and there are output files already
            # display the previous test details, and give the link
            for key in json_output.keys():
                if key.isnumeric():
                    message += self.mf_test_previous(int(key))
                    message += self.mf_test_json(json_output, int(key))

        else:  # the return message when check ends
            message = self.mf_test_end(check_type)

        if CONFIG_DATA["generate_output_file"]:
            self.write_msg_to_file(message, mail)

    def message_after_check_schema(self, output):
        """
        Generate a summary message based on the results of a schema validation check.

        Parameters:
        - output (dict): The summarized results from schema validation.

        Returns:
        - str: A message providing information about different property categories and metadata warnings.

        Example:
        >>> validation_results = {...}  # An example of summarized validation results
        >>> self.message_after_check_schema(validation_results)
        '
        These properties are well documented properties:

            dateCreated, dateModified, source, name, ...

        These properties are already used properties:

            openingHoursSpecification, startDate, ...

        No big issue with the named properties in general.

        Some warnings related to metadata:

        ...
        '

        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        results = output["sumup_results"]
        message = ""
        for key in self.CHECKED_PROPERTY_CASES[:-2]:
            if len(results[key]) != 0:
                msg = f"""
    These properties are {key} properties: 
        {self.newline + f"{' '*9}" + ", ".join(results[key])}
    """
                message += msg

        if len(results[self.CHECKED_PROPERTY_CASES[-1]]) != 0:
            message += f"""
    However, We highly suggest you to fix with these properties:
    
        {self.newline.join([" - " + text + self.newline + f"{' '*13}" + f"{', '.join(pps)}" for text, pps in results['Failed'].items()])}
            """
        else:
            message += f"""
    No big issue with the named properties in general.
            """

        if len(results[self.CHECKED_PROPERTY_CASES[-2]]) != 0:
            message += f"""
    Some warnings related to metadata:
    
{self.newline.join(["         - " + text for text in results['Metadata']])}
            """
        else:
            message += f"""
    No warning with metadata.        
            """
        return message

    def message_after_check_example(self, output):
        message = ""
        for _, pps in output["metadata"].items():
            if pps:
                msg = f"""
    
        {self.newline.join([" - " + text + self.newline + pp for text, pp in pps.items()])}
                """
                message += msg
        if not message:
            return f"""
    No big issue with the metadata in /examples.
        """
        return message

    def message_after_check(self, output: dict, test_number: int, is_param_check: bool = False) -> str:
        """
        Create return messages for parameters check, schema.json check
        """
        message = str()

        if is_param_check:
            message = output["cause"]
        elif test_number == 2:
            message = self.message_after_check_schema(output)
        else:
            message = ""

        return message

    ################################################
    # Test output json file related:
    #
    #       create, read, update, write json file, get json file url etc.
    ################################################
    def create_output_json(self, test_number, data_model_repo_url, mail, tz, meta_schema):
        """
        Create output json file for a specific check

        Parameters:
            test_number (int): the number of test, 1 - file structure check, 2 - schema.json check,
                            3 - examples check, 4 - other files check
            data_model_repo_url (str): the repository link to the data model
            mail (str): the mail of the user
            tz: timezone
            meta_schema (str): a link to metaSchema

        Returns:
            json_output_filepath (str): the path of the output json file
            output (dict): the output json dictionary
        """
        subject = self.extract_subject_raw_from_repo_url(data_model_repo_url)
        data_model = self.extract_datamodel_raw_from_repo_url(data_model_repo_url)

        # create the path
        # Just for now
        json_output_dir = "./mastercheck_output/"
        json_output_filepath = (json_output_dir +
                                f"{subject.strip('/').replace('/', '.')}_{data_model.strip('/').replace('/', '.')}"
                                f"_{mail}_{self.get_now(tz)}_{self.SUFFIX}.json")

        try:
            # if path exists already, which means the previous checks exist
            # get the previous check return
            output = self.read_output_json(json_output_filepath)
            output['lastModifiedTime'] = self.get_now_verbose(tz, '%Y-%m-%dT%H:%M:%S%z')

            self.send_message(test_number, mail, tz, check_type="start", json_output=output)
            self.send_message(test_number, mail, tz, check_type="previous", json_output=output)

        except FileNotFoundError:
            # create the metadata for json output
            output = dict()
            output['subject'] = subject
            output['data_model'] = data_model
            output['mail'] = mail
            output['date'] = self.get_now(tz, '%Y-%m-%dT%H:%M:%S%z')
            output['repoUrl'] = data_model_repo_url
            output['createdTime'] = self.get_now_verbose(tz, '%Y-%m-%dT%H:%M:%S%z')
            output['lastModifiedTime'] = self.get_now_verbose(tz, '%Y-%m-%dT%H:%M:%S%z')
            output['metaschema'] = meta_schema
            output['message'] = ""

            self.send_message(test_number, mail, tz, check_type="start", json_output=output)

        # write the current output into the file
        self.update_output_json(json_output_filepath, output)

        return json_output_filepath, output

    @staticmethod
    def read_output_json(json_output_filepath):
        """
        Read the json output file
        """
        with open(json_output_filepath, 'r') as file:
            output = load(file)
        return output

    @staticmethod
    def update_output_json(json_output_filepath, output):
        """
        Write the json output dictionary to the file
        """
        with open(json_output_filepath, 'w') as file:
            dump(output, file)

    def clean_test_data(self, json_output_filepath, test_number, logger):
        """
        Clean up the previous test and update in json output
        """
        output = self.read_output_json(json_output_filepath)

        try:
            output.pop(str(test_number))
            self.update_output_json(json_output_filepath, output)
        except KeyError as e:
            logger.warning(f"WARNING: The test_number {e} is not found in the output")

    def customized_json_dumps(self,
                              output: dict,
                              tz: timezone,
                              test_number: int,
                              json_output_filepath: str,
                              mail: str,
                              flag: bool = True,
                              is_param_check: bool = False) -> dict:
        """
        Create the json output at the end of each check according to the status

        Parameters:
            output (dict): the json output of the specific check
            tz (timezone): timezone
            test_number (int): the number of test, 1 - file structure check, 2 - schema.json check,
                            3 - examples check, 4 - other files check
            json_output_filepath (str): the file path to json output
            mail (str): the mail of the user generate_output_file (bool): whether we wanted to generate an output
            file with the content of the execution or just show the content in the log content.
            flag (bool): whether check is passed or failed, True is passed and False is failed
            is_param_check (bool): whether check is parameters check or not
        """
        output["testnumber"] = test_number
        output["testname"] = self.TESTS[test_number - 1]
        output["time"] = self.get_now_verbose(tz, '%Y-%m-%dT%H:%M:%S%z')

        # get the json output dictionary for all checks
        json_output = self.read_output_json(json_output_filepath)

        if self.generate_output_file:
            output['jsonUrl'] = self.get_json_output_url(json_output, test_number)

        # if the check is passed, update the "result" in json output to True
        if flag:
            output["result"] = flag

        output["message"] = self.message_after_check(output, test_number, is_param_check)

        # update the json output with the information of the specific check
        json_output[test_number] = output
        json_output["lastModifiedTime"] = self.get_now_verbose(tz, '%Y-%m-%dT%H:%M:%S%z')
        self.update_output_json(json_output_filepath, json_output)

        # create return message according to the status
        if self.generate_output_file:
            if flag:
                self.send_message(test_number, mail, tz, check_type="passed", json_output=json_output)
            else:
                self.send_message(test_number, mail, tz, check_type="failed", json_output=json_output)

        return output

    @staticmethod
    def get_json_output_url(json_output, test_number):
        """
        Generate the json output link
        """
        return (f"https://smartdatamodels.org/extra/get_test_json_output.php?subject="
                f"{json_output['subject'].strip('/').replace('/', '.')}&datamodel="
                f"{json_output['data_model'].strip('/').replace('/', '.')}&mail="
                f"{json_output['mail']}&date={json_output['date']}&testnumber={test_number}")

    @staticmethod
    def get_normalized_examples_url(file_path):
        """
        Generate the referral normalized examples link
        """
        return f"https://smartdatamodels.org/extra/mastercheck_output/{file_path.split('/')[-1]}"

    ################################################
    # Time related, two formats now
    ################################################
    @staticmethod
    def get_now(tz, my_format="%m%d"):
        now = datetime.now(tz=tz)
        formatted_date = now.strftime(my_format)  # MMDD
        return formatted_date

    def get_now_verbose(self, tz, apply_format="%Y-%m-%d %H:%M:%S"):
        return self.get_now(tz, apply_format)

    ################################################
    # To open json file when giving a url
    ################################################
    @staticmethod
    def open_json(file_url):
        """
        TODO import the function from python package by "from pysmartdatamodel.utils import *"
        """
        import json
        import requests
        if file_url[0:4] == "http":
            # it is a URL
            try:
                pointer = requests.get(file_url)
                return json.loads(pointer.content.decode('utf-8'))
            except Exception as e:
                print(e)
                return None

        else:
            # it is a file
            try:
                file = open(file_url, "r")
                return json.loads(file.read())
            except Exception as e:
                print(e)
                return None

    @staticmethod
    def open_jsonref(file_url):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        if file_url[0:4] == "http":
            # is a URL
            try:
                pointer = get(file_url)
                output = jsonref_loads(pointer.content.decode('utf-8'), load_on_repr=False, merge_props=True)
                return output
            except Exception as e:
                print(e)
                return ""
        else:
            # is a file
            try:
                with open(file_url, "r") as file:
                    data = jsonref_loads(file.read())
                return data
            except Exception as e:
                print(e)
                print(file_url)
                return ""

    ################################################
    # URL related
    #
    #   - existence of url
    #   - get existing urls
    #   - create urls
    #   - extract subject, data models information from urls
    ################################################
    @staticmethod
    def is_url_existed(url):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        try:
            pointer = get(url)
            if pointer.status_code == 200:
                return [True, pointer.text]
            else:
                return [False, pointer.status_code]
        except Exception as e:
            print(e)
            return [False, "wrong domain"]

    def get_other_files_raw(self, repo_url, checking_file):
        """
        Generate the other files link, such as notes.yaml
        """
        subject_raw = self.extract_subject_raw_from_repo_url(repo_url)
        data_model_raw = self.extract_datamodel_raw_from_repo_url(repo_url)
        return f"https://raw.githubusercontent.com/{subject_raw}/{data_model_raw}/{checking_file}"

    def get_context_jsonld_raw(self, repo_url):
        """
        Generate the context.jsonld link in raw version

        TODO update the new context format
        """
        subject_raw = self.extract_subject_raw_from_repo_url(repo_url)
        return f"https://raw.githubusercontent.com/{subject_raw}/master/context.jsonld"

    def get_schema_json_raw(self, repo_url):
        """
        Generate the schema.json link in raw version
        """
        subject_raw = self.extract_subject_raw_from_repo_url(repo_url)
        data_model_raw = self.extract_datamodel_raw_from_repo_url(repo_url)
        schema_url = f"https://raw.githubusercontent.com/{subject_raw}/{data_model_raw}/schema.json"
        return schema_url

    def create_example_url_raw(self, repo_url, checking_file):
        """
        Generate the examples link in raw version
        """
        subject_raw = self.extract_subject_raw_from_repo_url(repo_url)
        data_model_raw = self.extract_datamodel_raw_from_repo_url(repo_url)
        return f"https://raw.githubusercontent.com/{subject_raw}/{data_model_raw}/examples/{checking_file}"

    # only in smart-data-models repo
    # https://smart-data-models.github.io/subject/datamodel/schema.json
    def create_schema_json_url(self, repo_url):
        """
        Generate the schema.json link
        """
        subject = self.extract_subject_from_repo_url(repo_url)
        data_model = self.extract_datamodel_from_repo_url(repo_url)
        return f"https://smart-data-models.github.io/{subject}/{data_model}/schema.json"

    @staticmethod
    def extract_string_from_url(repo_url, left, right):
        """
        Extract string from url given the start and end
        """
        start = repo_url.find(left) + len(left)
        end = repo_url.find(right)
        return repo_url[start:end]

    def extract_subject_raw_from_repo_url(self, repo_url):
        """
        Extract name of subject from repository url in raw version

        Examples:
        >>> self.extract_subject_raw_from_repo_url(
        "https://github.com/smart-data-models/dataModel.Weather/tree/master/SeaConditions")
        "smart-data-models/dataModel.Weather"
        >>> self.extract_subject_raw_from_repo_url(
        "https://github.com/smart-data-models/dataModel.Ports/tree/53f24ff86216be9ad01c04f9133141f50dc8920c/BoatAuthorized")
        "smart-data-models/dataModel.Ports"
        >>> self.extract_subject_raw_from_repo_url(
        "https://github.com/smart-data-models/incubated/tree/master/CROSSSECTOR/DataSovereignty/AlgorithmAssessed")
        "smart-data-models/incubated"
        """
        if "/tree/" in repo_url:
            return self.extract_string_from_url(repo_url, "https://github.com/", "/tree/")
        elif "/blob/" in repo_url:
            return self.extract_string_from_url(repo_url, "https://github.com/", "/blob/")

    @staticmethod
    def extract_datamodel_raw_from_repo_url(repo_url):
        """
        Extract name of data model from repository url in raw version

        Examples:
        >>> SDMUtils.extract_datamodel_raw_from_repo_url(
        "https://github.com/smart-data-models/dataModel.Weather/tree/master/SeaConditions")
        "master/SeaConditions"
        >>> SDMUtils.extract_datamodel_raw_from_repo_url(
        "https://github.com/smart-data-models/dataModel.Ports/tree/53f24ff86216be9ad01c04f9133141f50dc8920c/BoatAuthorized")
        "53f24ff86216be9ad01c04f9133141f50dc8920c/BoatAuthorized"
        >>> SDMUtils.extract_datamodel_raw_from_repo_url(
        "https://github.com/smart-data-models/incubated/tree/master/CROSSSECTOR/DataSovereignty/AlgorithmAssessed")
        "CROSSSECTOR/DataSovereignty/AlgorithmAssessed"
        """
        start = int()

        if "/tree/" in repo_url:
            start = repo_url.find("/tree/") + len("/tree/")
        elif "/blob/" in repo_url:
            start = repo_url.find("/blob/") + len("/blob/")

        return repo_url[start:]

    def extract_subject_from_repo_url(self, repo_url):
        """
        Extract name of subject from repository url

        Examples:
        >>> self.extract_subject_from_repo_url(
        "https://github.com/smart-data-models/dataModel.Weather/tree/master/SeaConditions")
        "dataModel.Weather"
        >>> self.extract_subject_from_repo_url(
        "https://github.com/smart-data-models/dataModel.Ports/tree/53f24ff86216be9ad01c04f9133141f50dc8920c/BoatAuthorized")
        "dataModel.Ports"
        >>> self.extract_subject_from_repo_url(
        "https://github.com/smart-data-models/incubated/tree/master/CROSSSECTOR/DataSovereignty/AlgorithmAssessed")
        "incubated"
        """
        subject_raw = self.extract_subject_raw_from_repo_url(repo_url)
        return subject_raw.strip('/').split('/')[-1]

    def extract_datamodel_from_repo_url(self, repo_url):
        """
        Extract name of data model from repository url

        Examples:
        >>> self.extract_datamodel_from_repo_url(
        "https://github.com/smart-data-models/dataModel.Weather/tree/master/SeaConditions")
        "SeaConditions"
        >>> self.extract_datamodel_from_repo_url("https://github.com/smart-data-models/dataModel.Ports/tree/53f24ff86216be9ad01c04f9133141f50dc8920c/BoatAuthorized")
        "BoatAuthorized"
        >>> self.extract_datamodel_from_repo_url(
        "https://github.com/smart-data-models/incubated/tree/master/CROSSSECTOR/DataSovereignty/AlgorithmAssessed")
        "AlgorithmAssessed"
        """
        data_model_raw = self.extract_datamodel_raw_from_repo_url(repo_url)
        return data_model_raw.strip('/').split('/')[-1]

    ################################################
    # Payload parser
    ################################################
    def parse_description(self, schema_payload):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        output = {}
        purged_description = str(schema_payload["description"]).replace(chr(34), "")
        # process the description
        purged_description = sub(r'\.([A-Z])', r'. \1', purged_description)

        separated_description = purged_description.split(". ")
        copied_description = list.copy(separated_description)

        for descriptionPiece in separated_description:
            if descriptionPiece in self.propertyTypes:
                output["type"] = descriptionPiece
                copied_description.remove(descriptionPiece)
            elif descriptionPiece.find("Model:") > -1:
                copied_description.remove(descriptionPiece)
                output["model"] = descriptionPiece.replace("'", "").replace(
                    "Model:", "")

            if descriptionPiece.find("Units:") > -1:
                copied_description.remove(descriptionPiece)
                output["units"] = descriptionPiece.replace("'", "").replace(
                    "Units:", "")
        description = ". ".join(copied_description)

        return output, description

    @staticmethod
    def merge_duplicate_attributes(aa, bb):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        if bb:
            for key, values in bb.items():
                if key in aa:
                    aa[key].extend(values)
                else:
                    aa[key] = values
        return aa

    def parse_payload_v2(self, schema_payload, level):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        output = {}
        attributes = {level: []}
        if level == 1:
            if "allOf" in schema_payload:
                for index in range(len(schema_payload["allOf"])):
                    if "definitions" in schema_payload["allOf"][index]:
                        partial_output, partial_attr = self.parse_payload_v2(
                            schema_payload["allOf"][index]["definitions"], level + 1)
                        output = dict(output, **partial_output)
                    elif "properties" in schema_payload["allOf"][index]:
                        partial_output, partial_attr = self.parse_payload_v2(schema_payload["allOf"][index], level + 1)
                        output = dict(output, **partial_output["properties"])
                    else:
                        partial_output, partial_attr = self.parse_payload_v2(schema_payload["allOf"][index], level + 1)
                        output = dict(output, **partial_output)
                    attributes = self.merge_duplicate_attributes(attributes, partial_attr)
            if "anyOf" in schema_payload:
                for index in range(len(schema_payload["anyOf"])):
                    if "definitions" in schema_payload["anyOf"][index]:
                        partial_output, partial_attr = self.parse_payload_v2(
                            schema_payload["anyOf"][index]["definitions"], level + 1)
                        output = dict(output, **partial_output)
                    elif "properties" in schema_payload["anyOf"][index]:
                        partial_output, partial_attr = self.parse_payload_v2(schema_payload["anyOf"][index], level + 1)
                        output = dict(output, **partial_output["properties"])
                    else:
                        partial_output, partial_attr = self.parse_payload_v2(schema_payload["anyOf"][index], level + 1)
                        output = dict(output, **partial_output)
                    attributes = self.merge_duplicate_attributes(attributes, partial_attr)
            if "oneOf" in schema_payload:
                for index in range(len(schema_payload["oneOf"])):
                    if "definitions" in schema_payload["oneOf"][index]:
                        partial_output, partial_attr = (
                            self.parse_payload_v2(schema_payload["oneOf"][index]["definitions"], level + 1))

                        output = dict(output, **partial_output)
                    elif "properties" in schema_payload["oneOf"][index]:
                        partial_output, partial_attr = (
                            self.parse_payload_v2(schema_payload["oneOf"][index], level + 1))

                        output = dict(output, **partial_output["properties"])
                    else:
                        partial_output, partial_attr = (
                            self.parse_payload_v2(schema_payload["oneOf"][index], level + 1))

                        output = dict(output, **partial_output)
                    attributes = self.merge_duplicate_attributes(attributes, partial_attr)

            if "properties" in schema_payload:
                output, partial_attr = self.parse_payload_v2(schema_payload["properties"], level + 1)
                attributes = self.merge_duplicate_attributes(attributes, partial_attr)

        elif level < 8:
            if isinstance(schema_payload, dict):
                for sub_schema in schema_payload:
                    if sub_schema in ["allOf", "anyOf", "oneOf"]:
                        output[sub_schema] = []
                        for index in range(len(schema_payload[sub_schema])):
                            if "properties" in schema_payload[sub_schema][index]:
                                partial_output, partial_attr = (
                                    self.parse_payload_v2(schema_payload[sub_schema][index], level + 1))

                                output[sub_schema].append(partial_output["properties"])
                            else:
                                partial_output, partial_attr = (
                                    self.parse_payload_v2(schema_payload[sub_schema][index], level + 1))

                                output[sub_schema].append(partial_output)
                            attributes = self.merge_duplicate_attributes(attributes, partial_attr)

                    elif sub_schema == "properties":
                        output[sub_schema] = {}
                        for prop in schema_payload["properties"]:
                            try:
                                output[sub_schema][prop]
                            except KeyError as e:
                                self.logger.debug(f"Property {e} not found in output sub_schema '{sub_schema}'")
                                output[sub_schema][prop] = {}
                                attributes[level].append(prop)
                            for item in list(schema_payload["properties"][prop]):
                                if item in ["allOf", "anyOf", "oneOf"]:
                                    output[sub_schema][prop][item] = []
                                    for index in range(len(schema_payload[sub_schema][prop][item])):
                                        partial_output, partial_attr = (
                                            self.parse_payload_v2(schema_payload[sub_schema][prop][item][index],
                                                                  level + 1))

                                        output[sub_schema][prop][item].append(partial_output)
                                        attributes = self.merge_duplicate_attributes(attributes, partial_attr)
                                elif item == "description":
                                    self.logger.debug(f"Detected property description: {prop}")
                                    x_ngsi, description = self.parse_description(schema_payload[sub_schema][prop])
                                    output[sub_schema][prop][item] = description
                                    if x_ngsi:
                                        output[sub_schema][prop]["x-ngsi"] = x_ngsi

                                elif item == "items":
                                    output[sub_schema][prop][item], partial_attr = (
                                        self.parse_payload_v2(schema_payload[sub_schema][prop][item], level + 1))

                                    attributes = self.merge_duplicate_attributes(attributes, partial_attr)
                                elif item == "properties":
                                    output[sub_schema][prop][item], partial_attr = (
                                        self.parse_payload_v2(schema_payload[sub_schema][prop][item], level + 1))

                                    attributes = self.merge_duplicate_attributes(attributes, partial_attr)
                                elif item == "type":
                                    if schema_payload[sub_schema][prop][item] == "integer":
                                        output[sub_schema][prop][item] = "number"
                                    else:
                                        output[sub_schema][prop][item] = schema_payload[sub_schema][prop][item]
                                else:
                                    output[sub_schema][prop][item] = schema_payload[sub_schema][prop][item]

                    elif isinstance(schema_payload[sub_schema], dict):
                        attributes[level].append(sub_schema)
                        output[sub_schema], partial_attr = self.parse_payload_v2(schema_payload[sub_schema], level + 1)
                        attributes = self.merge_duplicate_attributes(attributes, partial_attr)
                    else:
                        if sub_schema == "description":
                            x_ngsi, description = self.parse_description(schema_payload)
                            output[sub_schema] = description
                            if x_ngsi:
                                output["x-ngsi"] = x_ngsi
                        else:
                            output[sub_schema] = schema_payload[sub_schema]

            elif isinstance(schema_payload, list):
                for index in range(len(schema_payload)):
                    partial_output, partial_attr = self.parse_payload_v2(schema_payload[index], level + 1)
                    output = dict(output, **partial_output)
                    attributes = self.merge_duplicate_attributes(attributes, partial_attr)
        else:
            return None, None

        return output, attributes

    ################################################
    # Convert a normalized json v2 file to key value format
    ################################################
    def normalized2keyvalues(self, normalized_payload, output, tz, test, json_output_filepath, mail):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        but has to customized a bit
        """
        normalized_dict = normalized_payload
        # normalized_dict = json.loads(normalizedPayload)
        tmp_output = {}
        # print(normalized_dict)
        for element in normalized_dict:
            # print(normalized_dict[element])
            try:
                value = normalized_dict[element]["value"]
                if isinstance(value, dict):
                    tmp_value = {}
                    for key in value.keys():
                        tmp_value[key] = value[key]["value"]
                    tmp_output[element] = tmp_value
                else:
                    tmp_output[element] = value
            except Exception as e:
                print(e)
                return self.conversion_failed(tmp_output=tmp_output,
                                              normalized_dict=normalized_dict,
                                              element=element,
                                              output=output,
                                              tz=tz,
                                              test=test,
                                              mail=mail,
                                              json_output_filepath=json_output_filepath)

                # tmp_output[element] = normalized_dict[element]
                # output["cause"] = f"Conversion failure"
                # output["time"] = str(datetime.now(tz=tz))
                # self.customized_json_dumps(output=output,
                #                            tz=tz,
                #                            test_number=test,
                #                            json_output_filepath=json_output_filepath,
                #                            mail=mail,
                #                            flag=False)
                # return False

        # print(json.dumps(output, indent=4, sort_keys=True))
        return tmp_output

    def normalized2keyvalues_v2(self, normalized_payload, output, tz, test, json_output_filepath, mail, level=0):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        normalized_dict = normalized_payload
        tmp_output = {}
        for element in normalized_dict:
            try:
                prop = normalized_dict[element]
                if isinstance(prop, list) and len(prop) > 0 and isinstance(prop[0], dict):
                    tmp_list = list()
                    for idx in range(len(prop)):
                        sub_output = (
                            self.normalized2keyvalues_v2(prop[idx], output, tz, test, json_output_filepath, mail,
                                                         level + 1))

                        if "type" in sub_output and "value" in sub_output:
                            tmp_list.append(sub_output["value"])
                        else:
                            tmp_list.append(sub_output)
                    tmp_output[element] = tmp_list
                elif isinstance(prop, dict):
                    if "@value" in prop:
                        tmp_output[element] = prop["@value"]
                    elif "value" in prop:
                        value = prop["value"]
                        if isinstance(value, dict):
                            tmp_output[element] = (
                                self.normalized2keyvalues_v2({"value": value},
                                                             output,
                                                             tz,
                                                             test,
                                                             json_output_filepath,
                                                             mail,
                                                             level + 1)
                            )["value"]

                        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                            tmp_list = []
                            for idx in range(len(value)):
                                if "type" in value[idx] and "value" in value[idx]:
                                    tmp_list.append(
                                        self.normalized2keyvalues_v2(value[idx],
                                                                     output,
                                                                     tz,
                                                                     test,
                                                                     json_output_filepath,
                                                                     mail,
                                                                     level + 1)["value"])
                                else:
                                    tmp_list.append(
                                        self.normalized2keyvalues_v2(value[idx],
                                                                     output,
                                                                     tz,
                                                                     test,
                                                                     json_output_filepath,
                                                                     mail,
                                                                     level + 1))
                            tmp_output[element] = tmp_list
                        else:
                            tmp_output[element] = value
                    elif "object" in prop:
                        tmp_output[element] = prop["object"]
                    elif isinstance(prop, dict):
                        tmp_output[element] = (
                            self.normalized2keyvalues_v2(prop, output, tz, test, json_output_filepath, mail, level + 1))
                    else:
                        tmp_output[element] = prop
                else:
                    tmp_output[element] = prop

            except Exception as e:
                print(e)
                return self.conversion_failed(cause="Conversion failed",
                                              output=output,
                                              tz=tz,
                                              test=test,
                                              mail=mail,
                                              json_output_filepath=json_output_filepath)
                # tmp_output[element] = normalized_dict[element]
                # output["cause"] = f"Conversion failed"
                # output["time"] = str(datetime.now(tz=tz))
                # self.customized_json_dumps(output=output,
                #                            tz=tz,
                #                            test_number=test,
                #                            json_output_filepath=json_output_filepath,
                #                            mail=mail,
                #                            flag=False)
                # return False

        return tmp_output

    def conversion_failed(self,
                          cause: str,
                          output: dict,
                          tz,
                          test: int,
                          mail: str,
                          json_output_filepath: str,
                          parameters: dict = None,
                          is_param_check: bool = False) -> bool:
        # tmp_output[element] = normalized_dict[element]
        if parameters is not None:
            output["parameters"] = parameters

        output["cause"] = cause
        output["time"] = str(datetime.now(tz=tz))
        self.customized_json_dumps(output=output,
                                   tz=tz,
                                   test_number=test,
                                   json_output_filepath=json_output_filepath,
                                   mail=mail,
                                   flag=False,
                                   is_param_check=is_param_check)
        return False

    def keyvalues2normalized_ld(self, keyvalues_payload, yaml_dict, detailed=True, level=0):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        import json

        def valid_date(date_string):
            if not ("T" in date_string) and ("Z" in date_string):
                try:
                    time.fromisoformat(date_string.replace('Z', '+00:00'))
                except Exception as e:
                    print(e)
                    return False, "Text"
                return True, "Time"

            else:
                date = date_string.split("T")[0]
                # print(date)
                try:
                    new_valid_date = match(r'^[0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4}$', date)
                    # print(new_valid_date)
                except ValueError:
                    return False, "Text"

                if new_valid_date is not None:
                    if len(date_string.split("T")) > 1:
                        return True, "DateTime"
                    return True, "Date"
                else:
                    return False, "Text"

        keyvalues_dict = keyvalues_payload
        output = {}
        # print(normalizedDict)
        for element in keyvalues_dict:
            if level == 0 and element in ["id", "type", "@context"]:
                continue

            item = {}
            if isinstance(keyvalues_dict[element], list):
                # it is an array
                item["type"] = yaml_dict[element]['x-ngsi']['type']
                if detailed:
                    if len(keyvalues_dict[element]) > 0 and isinstance(keyvalues_dict[element][0], dict):
                        tmp_list = []
                        for idx in range(len(keyvalues_dict[element])):
                            tmp_list.append(self.keyvalues2normalized_ld(keyvalues_dict[element][idx],
                                                                         yaml_dict[element][idx],
                                                                         level=level + 1))
                        item["value"] = tmp_list
                    else:
                        item["value"] = keyvalues_dict[element]
                else:
                    item["value"] = keyvalues_dict[element]
            elif isinstance(keyvalues_dict[element], dict):
                # it is an object
                # item["type"] = "object"
                if element == "location":
                    item["type"] = yaml_dict[element]['x-ngsi']['type']
                elif "type" in keyvalues_dict[element] and "coordinates" in keyvalues_dict[element]:
                    # location-like property
                    item["type"] = yaml_dict[element]['x-ngsi']['type']
                else:
                    item["type"] = yaml_dict[element]['x-ngsi']['type']
                if detailed:
                    item["value"] = self.keyvalues2normalized_ld(keyvalues_dict[element], yaml_dict[element],
                                                                 level=level + 1)
                else:
                    item["value"] = keyvalues_dict[element]
            elif isinstance(keyvalues_dict[element], str):
                date_flag, date_type = valid_date(keyvalues_dict[element])
                if date_flag:
                    # it is a date
                    item["type"] = yaml_dict[element]['x-ngsi']['type']
                    if date_type == "Date":
                        item["value"] = {"@type": "Date", "@value": keyvalues_dict[element]}
                    elif date_type == "Time":
                        item["value"] = {"@type": "Time", "@value": keyvalues_dict[element]}
                    else:
                        item["value"] = {"@type": "DateTime", "@value": keyvalues_dict[element]}
                else:
                    # it is a string
                    item["type"] = yaml_dict[element]['x-ngsi']['type']
                    item["value"] = keyvalues_dict[element]
            elif isinstance(keyvalues_dict[element], int) or isinstance(keyvalues_dict[element], float):
                # it is a number
                item["type"] = yaml_dict[element]['x-ngsi']['type']
                item["value"] = keyvalues_dict[element]
            elif keyvalues_dict[element]:
                # it is a boolean
                item["type"] = yaml_dict[element]['x-ngsi']['type']
                item["value"] = json.loads("true")
            elif not keyvalues_dict[element]:
                # it is a boolean
                item["type"] = yaml_dict[element]['x-ngsi']['type']
                item["value"] = json.loads("false")
            else:
                print("*** other type ***")
                print("I do not know what is it")
                print(keyvalues_dict[element])
                print("--- other type ---")

            output[element] = item

        if "id" in keyvalues_dict:
            output["id"] = keyvalues_dict["id"]

        if "type" in keyvalues_dict:
            output["type"] = keyvalues_dict["type"]

        if "@context" in keyvalues_dict:
            output["@context"] = keyvalues_dict["@context"]

        return output

    def keyvalues2normalized_v2(self, keyvalues_payload, detailed=True):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """
        import json

        def valid_date(date_string):
            import re
            date = date_string.split("T")[0]
            # print(date)
            try:
                new_valid_date = re.match(r'^[0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4}$', date)
                # print(new_valid_date)
            except ValueError:
                return False

            if new_valid_date is not None:
                return True
            else:
                return False

        keyvalues_dict = keyvalues_payload
        output = {}
        # print(normalizedDict)
        for element in keyvalues_dict:
            item = {}
            if isinstance(keyvalues_dict[element], list):
                # it is an array
                # item["type"] = "array"
                item["type"] = "StructuredValue"
                if detailed:
                    if len(keyvalues_dict[element]) > 0 and isinstance(keyvalues_dict[element][0], dict):
                        tmp_list = list()
                        for idx in range(len(keyvalues_dict[element])):
                            tmp_list.append(self.keyvalues2normalized_v2(keyvalues_dict[element][idx]))
                        item["value"] = tmp_list
                    else:
                        item["value"] = keyvalues_dict[element]
                else:
                    item["value"] = keyvalues_dict[element]
            elif isinstance(keyvalues_dict[element], dict):
                # it is an object
                # item["type"] = "object"
                if element == "location":
                    item["type"] = "geo:json"
                else:
                    item["type"] = "StructuredValue"
                if detailed:
                    item["value"] = self.keyvalues2normalized_v2(keyvalues_dict[element])
                else:
                    item["value"] = keyvalues_dict[element]
            elif isinstance(keyvalues_dict[element], str):
                if valid_date(keyvalues_dict[element]):
                    # it is a date
                    # item["format"] = "date-time"
                    item["type"] = "DateTime"
                else:
                    # it is a string
                    # item["type"] = "string"
                    item["type"] = "Text"

                item["value"] = keyvalues_dict[element]
            elif isinstance(keyvalues_dict[element], int) or isinstance(keyvalues_dict[element], float):
                # it is a number
                # item["type"] = "number"
                item["type"] = "Number"
                item["value"] = keyvalues_dict[element]
            elif keyvalues_dict[element]:
                # it is a boolean
                # item["type"] = "boolean"
                item["type"] = "Boolean"
                item["value"] = json.loads("true")
            elif not keyvalues_dict[element]:
                # it is a boolean
                # item["type"] = "boolean"
                item["type"] = "Boolean"
                item["value"] = json.loads("false")
            else:
                print("*** other type ***")
                print("I do now know what is it")
                print(keyvalues_dict[element])
                print("--- other type ---")

            output[element] = item

        if "id" in output:
            output["id"] = output["id"]["value"]

        if "type" in output:
            output["type"] = output["type"]["value"]

        if "@context" in output:
            output["@context"] = output["@context"]["value"]

        return output

    ################################################
    # Check key-value and normalized format
    ################################################
    @staticmethod
    def check_key_value(payload):
        """
        Check the key-value format of examples.

        Parameters:
            payload (dict): the payload of examples

        Returns:
            Tuple((str, list), bool): return an empty list with bool True if the check passed
                                    return a list of failed properties with bool False if the check failed
                                    return a string 'Unable to read' with bool False if the payload is wrong
        """
        props = []
        try:
            for prop, item in payload.items():
                if isinstance(item, dict):
                    if "type" in item.keys() and "value" in item.keys():
                        props.append(prop)
            if len(props) == 0:
                return props, True
            else:
                return props, False
        except Exception as e:
            print(e)
            return 'Unable to read', False

    @staticmethod
    def check_normalized(payload):
        """
        Check the normalized format of examples.

        Parameters:
            payload (dict): the payload of examples

        Returns:
            Tuple((str, list), bool): return an empty list with bool True if the check passed
                                    return a list of failed properties with bool False if the check failed
                                    return a string 'Unable to read' with bool False if the payload is wrong
        """
        props = []
        try:
            for prop, item in payload.items():
                if prop in ['id', 'type', '@context']:
                    continue

                if not isinstance(item, dict):
                    props.append(prop)
                else:
                    if "type" not in item.keys():
                        props.append(prop)

                    if ("value" not in item.keys()) and ("object" not in item.keys()):
                        props.append(prop)

            if len(props) == 0:
                return props, True
            else:
                return props, False
        except Exception as e:
            print(e)
            return 'Unable to read', False

    ################################################
    # parameters check related
    ################################################
    def check_parameters(self,
                         output,
                         tz,
                         json_output_filepath,
                         schema_url="",
                         mail="",
                         test="",
                         meta_schema="",
                         tag="",
                         additional_properties=False):

        schema_dict = dict()
        yaml_dict = dict()

        # check schemaUrl
        if schema_url:
            # validate inputs
            exists_schema = self.is_url_existed(schema_url)

            # url provided is an existing url
            if not exists_schema[0]:
                output["cause"] = f"Cannot find the {tag} at " + schema_url
                output["time"] = str(datetime.now(tz=tz))
                self.customized_json_dumps(output=output,
                                           tz=tz,
                                           test_number=int(test),
                                           json_output_filepath=json_output_filepath,
                                           mail=mail,
                                           flag=False,
                                           is_param_check=True)
                return False

            # url is actually a valid json
            try:
                schema_dict = loads(exists_schema[1])
            except JSONDecodeError as e:
                return self.conversion_failed(cause=f"{tag} {schema_url} is not a valid json. {e}",
                                              parameters={"schemaUrl": schema_url, "mail": mail, "test": test},
                                              output=output,
                                              tz=tz,
                                              test=int(test),
                                              mail=mail,
                                              json_output_filepath=json_output_filepath,
                                              is_param_check=True)


                # output["cause"] = f"{tag} {schema_url} is not a valid json. {e}"
                # output["time"] = str(datetime.now(tz=tz))
                # output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                # self.customized_json_dumps(output=output,
                #                            tz=tz,
                #                            test_number=int(test),
                #                            json_output_filepath=json_output_filepath,
                #                            mail=mail,
                #                            flag=False,
                #                            is_param_check=True)
                # return False

            # test that it is a valid schema against the metaschema
            try:
                schema = self.open_jsonref(schema_url)
                # echo("len of schema", len(str(schema)))
                # echo("schema", schema)
                if not bool(schema):
                    return self.conversion_failed(cause=f"json {tag} returned empty (wrong $ref?)",
                                                  parameters={"schemaUrl": schema_url, "mail": mail, "test": test},
                                                  output=output,
                                                  tz=tz,
                                                  test=int(test),
                                                  mail=mail,
                                                  json_output_filepath=json_output_filepath,
                                                  is_param_check=True)

                    # output["cause"] = f"json {tag} returned empty (wrong $ref?)"
                    # output["time"] = str(datetime.now(tz=tz))
                    # output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                    # self.customized_json_dumps(output=output,
                    #                            tz=tz,
                    #                            test_number=int(test),
                    #                            json_output_filepath=json_output_filepath,
                    #                            mail=mail,
                    #                            flag=False,
                    #                            is_param_check=True)
                    # return False
            except Exception as e:
                print(e)
                return self.conversion_failed(cause=f"json {tag} cannot be fully loaded",
                                              parameters={"schemaUrl": schema_url, "mail": mail, "test": test},
                                              output=output,
                                              tz=tz,
                                              test=int(test),
                                              mail=mail,
                                              json_output_filepath=json_output_filepath,
                                              is_param_check=True)

                # output["cause"] = f"json {tag} cannot be fully loaded"
                # output["time"] = str(datetime.now(tz=tz))
                # output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                # self.customized_json_dumps(output=output,
                #                            tz=tz,
                #                            test_number=int(test),
                #                            json_output_filepath=json_output_filepath,
                #                            mail=mail,
                #                            flag=False,
                #                            is_param_check=True)
                # return False

            try:
                yaml_dict, attributes = self.parse_payload_v2(schema, 1)
                # global schema_json_yaml_dict
                if tag == "schema":
                    self.schema_json_yaml_dict = yaml_dict.copy()
            except Exception as e:
                print(e)
                output["cause"] = f"{tag} cannot be loaded (possibly invalid $ref)"
                output["time"] = str(datetime.now(tz=tz))
                output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                self.customized_json_dumps(output=output,
                                           tz=tz,
                                           test_number=int(test),
                                           json_output_filepath=json_output_filepath,
                                           mail=mail,
                                           flag=False,
                                           is_param_check=True)
                return False

            # check the duplicated attributes
            if tag == "schema" and len(attributes[2]) != len(set(attributes[2])):

                def find_duplicates(input_list):
                    """
                    Find and output the duplicated values inside a list.
                    Args:
                        input_list (list): The list to search for duplicates in.
                    Returns:
                        list: A list containing the duplicated values found in the input list.
                    """
                    seen = set()
                    duplicates = set()

                    for item in input_list:
                        if item in seen:
                            duplicates.add(item)
                        else:
                            seen.add(item)

                    return list(duplicates)

                cause = (f"Duplicated attributes (User-defined properties is duplicated with system-defined "
                         f"properties:\n\t{', '.join(find_duplicates(attributes[2]))}")

                return self.conversion_failed(cause=cause,
                                              output=output,
                                              parameters={"schemaUrl": schema_url, "mail": mail, "test": test},
                                              tz=tz,
                                              test=int(test),
                                              mail=mail,
                                              json_output_filepath=json_output_filepath,
                                              is_param_check=True)

                # output["cause"] = (f"Duplicated attributes (User-defined properties is duplicated with system-defined "
                #                                    f"properties):\n\t{', '.join(find_duplicates(attributes[2]))}")
                #
                # output["time"] = str(datetime.now(tz=tz))
                # output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                # self.customized_json_dumps(output=output,
                #                            tz=tz,
                #                            test_number=int(test),
                #                            json_output_filepath=json_output_filepath,
                #                            mail=mail,
                #                            flag=False,
                #                            is_param_check=True)
                # return False

            # key-value and normalized format checking
            if "normalized.json" not in schema_url:
                # key-value
                props, flag = self.check_key_value(schema)
                if isinstance(props, str):
                    output["cause"] = f"{props} in {schema_url.split('/')[-1]}."
                    output["time"] = str(datetime.now(tz=tz))
                    output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                    self.customized_json_dumps(output=output,
                                               tz=tz,
                                               test_number=int(test),
                                               json_output_filepath=json_output_filepath,
                                               mail=mail,
                                               flag=False,
                                               is_param_check=True)
                    return False
                else:
                    if not flag:
                        output["cause"] = f"{', '.join(props)} should be in key-value format"
                        output["time"] = str(datetime.now(tz=tz))
                        output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                        self.customized_json_dumps(output=output,
                                                   tz=tz,
                                                   test_number=int(test),
                                                   json_output_filepath=json_output_filepath,
                                                   mail=mail,
                                                   flag=False,
                                                   is_param_check=True)
                        return False
            else:
                # normalized format
                props, flag = self.check_normalized(schema)
                if isinstance(props, str):
                    output["cause"] = f"{props} in {schema_url.split('/')[-1]}."
                    output["time"] = str(datetime.now(tz=tz))
                    output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                    self.customized_json_dumps(output=output,
                                               tz=tz,
                                               test_number=int(test),
                                               json_output_filepath=json_output_filepath,
                                               mail=mail,
                                               flag=False,
                                               is_param_check=True)
                    return False
                else:
                    if not flag:
                        output["cause"] = (
                            f"{', '.join(props)} should be in normalized format, can be caused by missing "
                            f"`type` or missing `value` or `object`")

                        output["time"] = str(datetime.now(tz=tz))
                        output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                        self.customized_json_dumps(output=output,
                                                   tz=tz,
                                                   test_number=int(test),
                                                   json_output_filepath=json_output_filepath,
                                                   mail=mail,
                                                   flag=False,
                                                   is_param_check=True)
                        return False

            if schema_url.endswith("schema.json"):
                try:
                    validate(instance=schema, schema=meta_schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
                except ValidationError as err:
                    # print(err)
                    output["cause"] = f"{tag} does not validate as a json schema"
                    output["time"] = str(datetime.now(tz=tz))
                    output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                    output["errorSchema"] = str(err)
                    self.customized_json_dumps(output=output,
                                               tz=tz,
                                               test_number=int(test),
                                               json_output_filepath=json_output_filepath,
                                               mail=mail,
                                               flag=False,
                                               is_param_check=True)
                    return False
            else:
                try:
                    # Add additionalProperties
                    if not additional_properties:
                        # tmp_schema = {}
                        # tmp_schema["type"] = "object"
                        # tmp_schema["properties"] = {}
                        # for idx in range(len(metaSchema["allOf"])):
                        #     tmp_schema["properties"] = dict(tmp_schema["properties"],
                        #                                     **metaSchema["allOf"][idx]["properties"])
                        #
                        # tmp_schema["additionalProperties"] = False
                        # metaSchema["allOf"] = [tmp_schema]

                        def flatten_all_of(my_schema):
                            new_tmp_schema = dict()
                            new_tmp_schema["properties"] = dict()
                            for idx in range(len(my_schema["allOf"])):
                                if "allOf" in my_schema["allOf"][idx]:
                                    tmp_output = flatten_all_of(my_schema["allOf"][idx])
                                    new_tmp_schema["properties"] = \
                                        (dict(new_tmp_schema["properties"], **tmp_output["properties"]))

                                if "properties" in my_schema["allOf"][idx]:
                                    new_tmp_schema["properties"] = \
                                        (dict(new_tmp_schema["properties"], **my_schema["allOf"][idx]["properties"]))

                            return new_tmp_schema

                        if "allOf" in meta_schema:
                            tmp_schema = flatten_all_of(meta_schema)
                            tmp_schema["additionalProperties"] = False
                            meta_schema["allOf"] = [tmp_schema]
                        elif "properties" in meta_schema:
                            meta_schema["additionalProperties"] = False

                    if "example-normalized" in schema_url:
                        result = self.normalized2keyvalues_v2(schema, output, tz, test, json_output_filepath, mail)

                        if not result:
                            return result
                        schema = result

                    if "@context" in schema:
                        schema.pop("@context")

                    validate(instance=schema, schema=meta_schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
                except ValidationError as err:
                    # print(err)
                    spacer = '\n'
                    output["cause"] = f"{tag} does not validate as a json schema. {str(err).split(spacer)[0]}"
                    output["time"] = str(datetime.now(tz=tz))
                    output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                    output["errorSchema"] = str(err)
                    self.customized_json_dumps(output=output,
                                               tz=tz,
                                               test_number=int(test),
                                               json_output_filepath=json_output_filepath,
                                               mail=mail,
                                               flag=False,
                                               is_param_check=True)
                    return False
                except SchemaError as err:
                    spacer = '\n'
                    output["cause"] = f"schema.json error while validating the {tag}. {str(err).split(spacer)[0]}"
                    output["time"] = str(datetime.now(tz=tz))
                    output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                    output["errorSchema"] = str(err)
                    self.customized_json_dumps(output=output,
                                               tz=tz,
                                               test_number=int(test),
                                               json_output_filepath=json_output_filepath,
                                               mail=mail,
                                               flag=False,
                                               is_param_check=True)
                    return False
                except Exception as err:
                    spacer = '\n'
                    output["cause"] = f"Exception occurs while validating the {tag}. {str(err).split(spacer)[0]}"
                    output["time"] = str(datetime.now(tz=tz))
                    output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                    output["errorSchema"] = str(err)
                    self.customized_json_dumps(output=output,
                                               tz=tz,
                                               test_number=int(test),
                                               json_output_filepath=json_output_filepath,
                                               mail=mail,
                                               flag=False,
                                               is_param_check=True)
                    return False

        # check email
        if mail:
            # mail is a real email
            if not checkers.is_email(mail):
                output["cause"] = "mail " + mail + " is not a valid email"
                output["time"] = str(datetime.now(tz=tz))
                output["parameters"] = {"schemaUrl": schema_url, "mail": mail, "test": test}
                self.customized_json_dumps(output=output,
                                           tz=tz,
                                           test_number=int(test),
                                           json_output_filepath=json_output_filepath,
                                           mail=mail,
                                           flag=False,
                                           is_param_check=True)
                return False

        return output, schema_dict, yaml_dict

    def is_valid_yaml(self, output, tz, json_output_filepath, yaml_url="", mail="", test="", tag="") \
            -> [bool, dict, dict]:
        """
        Process the model.yaml file
        """
        exists_yaml = self.is_url_existed(yaml_url)

        # url provided is an existing url
        if not exists_yaml[0]:
            output["cause"] = f"Cannot find the {tag} at " + yaml_url
            output["time"] = str(datetime.now(tz=tz))
            self.customized_json_dumps(output=output,
                                       tz=tz,
                                       test_number=int(test),
                                       json_output_filepath=json_output_filepath,
                                       mail=mail,
                                       flag=False,
                                       is_param_check=True)
            return False, output, dict()

        # url is actually a json
        try:
            yaml_dict = safe_load(exists_yaml[1])
        except ValueError:
            output["cause"] = f"{tag} " + yaml_url + " is not a valid json"
            output["time"] = str(datetime.now(tz=tz))
            output["parameters"] = {"schemaUrl": yaml_url, "mail": mail, "test": test}
            self.customized_json_dumps(output=output,
                                       tz=tz,
                                       test_number=int(test),
                                       json_output_filepath=json_output_filepath,
                                       mail=mail,
                                       flag=False,
                                       is_param_check=True)
            return False, output, dict()

        return True, output, yaml_dict

    ################################################
    # generate examples for referral
    ################################################
    def generate_examples(self,
                          example_v2_normalized_url,
                          example_ld_normalized_url,
                          output,
                          tz,
                          test,
                          json_output_filepath,
                          mail):
        """
        Generate the referral examples
        """

        # global schema_json_yaml_dict, example_v2_output_filepath, exampleLDOutput_filepath

        base_v2_normalized = self.open_json(example_v2_normalized_url)
        base_ld_normalized = self.open_json(example_ld_normalized_url)

        # convert normalized format into key-value format and then convert it back
        # in order to get the correct type for ngsi-v2
        example_nl2_kv = self.normalized2keyvalues_v2(base_v2_normalized, output, tz, test, json_output_filepath, mail)
        example_v2_normalized = self.keyvalues2normalized_v2(example_nl2_kv, detailed=False)
        # convert normalized format into key-value format and then convert it back
        # in order to get the correct type for ngsi-ld
        example_nl2_kv = self.normalized2keyvalues_v2(base_ld_normalized, output, tz, test, json_output_filepath, mail)
        example_ld_normalized = self.keyvalues2normalized_ld(example_nl2_kv, self.schema_json_yaml_dict, detailed=False)

        self.example_v2_output_filepath = json_output_filepath.replace(".json", "_example-normalized.json")
        self.exampleLDOutput_filepath = json_output_filepath.replace(".json", "_example-normalized.jsonld")

        self.update_output_json(self.example_v2_output_filepath, example_v2_normalized)
        self.update_output_json(self.exampleLDOutput_filepath, example_ld_normalized)

    def get_check_property_cases(self):
        return self.CHECKED_PROPERTY_CASES
