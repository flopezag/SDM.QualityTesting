from smartdatamodels.utils import (send_message, get_schema_json_raw, create_example_url_raw, check_parameters,
                                   open_jsonref, message_after_check_example, customized_json_dumps, generate_examples)
from smartdatamodels.MD_exist_v1 import is_metadata_existed_examples

# FL stands for inside file check for one data model
# this python file is focused on files under the examples folder
# TODO: include geojson example in the future
CHECK_EXAMPLES = [
    'example.json',
    'example.jsonld', 
    'example-normalized.json',
    'example-normalized.jsonld'
    ]


def check_fl_examples(data_model_repo_url, tz, test_number, mail, json_output_filepath):
    """
    Check files examples given the data model link
    """

    send_message(test_number=test_number,
                 mail=mail,
                 tz=tz,
                 check_type="loading")

    output = {"result": False}  # the json answering the test

    raw_schema_url = get_schema_json_raw(data_model_repo_url)
    meta_schema = open_jsonref(raw_schema_url)

    # go through all the files
    for checking_file in CHECK_EXAMPLES:

        raw_example_url = create_example_url_raw(data_model_repo_url, checking_file)
        
        send_message(test_number=test_number,
                     mail=mail,
                     tz=tz,
                     check_type="processing",
                     json_output=None,
                     sub_test_name=f"{checking_file} check")
        
        # from normalized to key-value
        # validate the examples and schema.json
        cf_output = {"result": False}

        # check the parameters
        # 1. whether example file is readable
        # 2. whether example payload is valid with schema, additional properties is not allowed
        # 3. whether properties are duplicated defined
        result = check_parameters(output=cf_output,
                                  tz=tz,
                                  json_output_filepath=json_output_filepath,
                                  schema_url=raw_example_url,
                                  mail=mail,
                                  test=test_number,
                                  meta_schema=meta_schema,
                                  tag=checking_file)
        
        # if result is false, then there exists mentioned errors
        if not result:
            return result

        # if result is true, return
        # cf_output: the json output dictionary
        # example_dict: the example dictionary
        cf_output, example_dict, _ = result
        cf_output["result"] = True

        # check the metadata of examples
        if checking_file.endswith("ld"):
            # check id, type, @context
            cf_output = is_metadata_existed_examples(cf_output,
                                                     example_dict,
                                                     data_model_repo_url)
        else:
            # check id, type
            cf_output = is_metadata_existed_examples(cf_output,
                                                     example_dict,
                                                     data_model_repo_url)
        
        output[checking_file] = cf_output

        if cf_output["metadata"]:
            # if metadata is not empty, then the test is failed, return the failed message
            output["cause"] = message_after_check_example(cf_output)
            customized_json_dumps(output, tz, test_number, json_output_filepath, mail, flag=False)
            return False

    try:
        # generate examples referral for example-normalized.json and example-normalized.jsonld
        generate_examples(create_example_url_raw(data_model_repo_url, 'example-normalized.json'),
                          create_example_url_raw(data_model_repo_url, 'example-normalized.jsonld'),
                          output, tz, test_number, json_output_filepath, mail)
    except Exception as e:
        print(e)
        print("Error when generating examples")

    customized_json_dumps(output, tz, test_number, json_output_filepath, mail)

    return True
