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
from smartdatamodels.utils import is_url_existed, customized_json_dumps, send_message


class CheckStructure:
    def __init__(self, logger, data_model_repo_url, mail, json_output_filepath, generate_output_file=False):
        self.logger = logger
        self.data_model_repo_url = data_model_repo_url
        self.mail = mail
        self.json_output_filepath = json_output_filepath
        self.generate_output_file = generate_output_file

    # url: check whether return 200
    def check_fs_minimal(self, tz, test_number):
        """
        Check the file structure to meet the minimal requirements
            - examples/
                - example-normalized.json or example-normalized.jsonId
            - schema.json
        """

        output = {"result": False}  # the json answering the test

        examples = (
            is_url_existed(self.data_model_repo_url + "/examples", "examples"))[0]

        schema_json = (
            is_url_existed(self.data_model_repo_url + "/schema.json", "schema.json"))[0]

        normalized_json = (
            is_url_existed(self.data_model_repo_url + "/examples/example-normalized.json",
                           "example-normalized.json"))[0]

        normalized_jsonld = (
            is_url_existed(self.data_model_repo_url + "/examples/example-normalized.jsonld",
                           "example-normalized.jsonld"))[0]

        if not examples:
            output["cause"] = (f"{self.data_model_repo_url.split('/')[-1]} "
                               f"Missing examples folder: Cannot open the url at "
                               f"{self.data_model_repo_url}/examples")

            output["time"] = str(datetime.now(tz=tz))
            customized_json_dumps(output=output,
                                  tz=tz,
                                  test_number=test_number,
                                  json_output_filepath=self.json_output_filepath,
                                  mail=self.mail,
                                  flag=False,
                                  generate_output_file=self.generate_output_file)

            return False

        if not schema_json:
            output["cause"] = (f"{self.data_model_repo_url.split('/')[-1]} Missing schema.json: Cannot open the url at "
                               f"{self.data_model_repo_url}/schema.json")

            output["time"] = str(datetime.now(tz=tz))
            customized_json_dumps(output=output,
                                  tz=tz,
                                  test_number=test_number,
                                  json_output_filepath=self.json_output_filepath,
                                  mail=self.mail,
                                  flag=False,
                                  generate_output_file=self.generate_output_file)

            return False

        if not (normalized_json | normalized_jsonld):
            output["cause"] = (f"{self.data_model_repo_url.split('/')[-1]} "
                               f"Missing example-normalized.json or example-normalized.jsonld: at least one is a must")

            output["time"] = str(datetime.now(tz=tz))
            customized_json_dumps(output=output,
                                  tz=tz,
                                  test_number=test_number,
                                  json_output_filepath=self.json_output_filepath,
                                  mail=self.mail,
                                  flag=False,
                                  generate_output_file=self.generate_output_file)

            return False

        customized_json_dumps(output=output,
                              tz=tz,
                              test_number=test_number,
                              json_output_filepath=self.json_output_filepath,
                              mail=self.mail,
                              generate_output_file=self.generate_output_file)

        return True

    def check_fs_normal(self, tz, test_number):
        """
        Check the file structure to meet the normal requirements
            - examples/
                - example.json
                - example.jsonld
                - example-normalized.json
                - example-normalized.jsonId
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
                - example-normalized.jsonId
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
            send_message(test_number, self.mail, tz, check_type="loading")

        if check_type == "minimal":
            #     def check_fs_minimal(self, tz, test_number):
            return self.check_fs_minimal(tz=tz, test_number=test_number)
        elif check_type == "normal":
            return self.check_fs_normal(tz=tz, test_number=test_number)
        elif check_type == "full":
            return self.check_fs_full(tz=tz, test_number=test_number)
