from smartdatamodels.utils import send_message, get_other_files_raw, is_valid_yaml, customized_json_dumps


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

    def check_fl_others(self, tz, test_number):
        """
        Check other files given the data model link
        """

        if self.generate_output_file:
            send_message(test_number, self.mail, tz, check_type="loading")

        output = {"result": False}  # the json answering the test

        # go through all the files
        for checking_file in self.CHECK_OTHERS:
            file_url = get_other_files_raw(self.data_model_repo_url, checking_file)

            # check whether yaml file is valid
            cf_output = dict()
            result = is_valid_yaml(output=cf_output,
                                   tz=tz,
                                   json_output_filepath=self.json_output_filepath,
                                   yaml_url=file_url,
                                   mail=self.mail,
                                   test=test_number,
                                   tag="yamls")

            if not result:
                return result

            # cf_output, yaml_dict = result

            if self.generate_output_file:
                send_message(test_number=test_number,
                             mail=self.mail,
                             tz=tz,
                             check_type="processing",
                             json_output=None,
                             sub_test_name=f"{checking_file} check")

            # TODO: check there's an email in the ADOPTERS.yaml file

        customized_json_dumps(output=output,
                              tz=tz,
                              test_number=test_number,
                              json_output_filepath=self.json_output_filepath,
                              mail=self.mail,
                              generate_output_file=self.generate_output_file)

        return True
