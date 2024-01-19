from smartdatamodels.utils import send_message, get_other_files_raw, is_valid_yaml, customized_json_dumps

# FL stands for inside file check for one data model
# this python file is focused on other files
# like notes.yaml, ADOPTERS.yaml, CONTRIBUTORS.yaml, LICENSE.md
CHECK_OTHERS = [
    "notes.yaml",
    "ADOPTERS.yaml",
    ]


def check_fl_others(data_model_repo_url, tz, test_number, mail, json_output_filepath):
    """
    Check other files given the data model link
    """

    send_message(test_number, mail, tz, check_type="loading")

    output = {"result": False}  # the json answering the test

    # go through all the files
    for checking_file in CHECK_OTHERS:
        file_url = get_other_files_raw(data_model_repo_url, checking_file)
        
        # check whether yaml file is valid
        cf_output = dict()
        result = is_valid_yaml(output=cf_output,
                               tz=tz,
                               json_output_filepath=json_output_filepath,
                               yaml_url=file_url,
                               mail=mail,
                               test=test_number,
                               tag="yamls")
        
        if not result:
            return result
    
        cf_output, yaml_dict = result
        send_message(test_number=test_number,
                     mail=mail,
                     tz=tz,
                     check_type="processing",
                     json_output=None,
                     sub_test_name=f"{checking_file} check")
        
        # TODO: check there's an email in the ADOPTERS.yaml file

    customized_json_dumps(output, tz, test_number, json_output_filepath, mail)

    return True
