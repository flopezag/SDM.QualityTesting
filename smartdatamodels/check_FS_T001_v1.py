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


# url: check whether return 200
def check_fs_minimal(file_url, tz, test_number, mail, json_output_filepath):
    """
    Check the file structure to meet the minimal requirements
        - examples/
            - example-normalized.json or example-normalized.jsonId
        - schema.json
    """

    output = {"result": False}  # the json answering the test

    examples = (
        is_url_existed(file_url + "/examples", "examples"))[0]

    schema_json = (
        is_url_existed(file_url + "/schema.json", "schema.json"))[0]

    normalized_json = (
        is_url_existed(file_url + "/examples/example-normalized.json", "example-normalized.json"))[0]

    normalized_jsonld = (
        is_url_existed(file_url + "/examples/example-normalized.jsonld", "example-normalized.jsonld"))[0]
    
    if not examples:
        output["cause"] = (f"{file_url.split('/')[-1]} Missing examples folder: Cannot open the url at "
                           f"{file_url}/examples")

        output["time"] = str(datetime.now(tz=tz))
        customized_json_dumps(output, tz, test_number, json_output_filepath, mail, flag=False)
        
        return False
    
    if not schema_json:
        output["cause"] = (f"{file_url.split('/')[-1]} Missing schema.json: Cannot open the url at "
                           f"{file_url}/schema.json")

        output["time"] = str(datetime.now(tz=tz))
        customized_json_dumps(output, tz, test_number, json_output_filepath, mail, flag=False)
        
        return False
    
    if not (normalized_json | normalized_jsonld):
        output["cause"] = (f"{file_url.split('/')[-1]} Missing example-normalized.json or example-normalized.jsonld: "
                           f"at least one is a must")

        output["time"] = str(datetime.now(tz=tz))
        customized_json_dumps(output, tz, test_number, json_output_filepath, mail, flag=False)
        
        return False

    customized_json_dumps(output, tz, test_number, json_output_filepath, mail)
    
    return True


def check_fs_normal():
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


def check_fs_full():
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


def check_file_structure(file_url, tz, test_number, mail, json_output_filepath, check_type="minimal"):
    """
    Check the file structure
    """

    send_message(test_number, mail, tz, check_type="loading")
    
    if check_type == "minimal":
        return check_fs_minimal(file_url, tz, test_number, mail, json_output_filepath)
    elif check_type == "normal":
        return check_fs_normal()
    elif check_type == "full":
        return check_fs_full()
