# FL stands for inside file check for one data model
# this python file is focused on schema.json file

from smartdatamodels.utils import (get_schema_json_raw, send_message, open_jsonref, check_parameters,
                                   customized_json_dumps, CHECKED_PROPERTY_CASES)
from smartdatamodels.PC_well_documented_v1 import is_well_documented
from smartdatamodels.PC_exist_already_v1 import is_property_already_existed
from smartdatamodels.MD_reported_v1 import is_metadata_properly_reported
from smartdatamodels.MD_exist_v1 import is_metadata_existed
from common.config import CONFIG_DATA


def check_fl_schema_json(data_model_repo_url, tz, test_number, mail, json_output_filepath):
    """
    Check file schema.json given the data model link
    """

    send_message(test_number, mail, tz, check_type="loading")

    output = {"result": False}  # the json answering the test

    raw_schema_url = get_schema_json_raw(data_model_repo_url)

    meta_schema = CONFIG_DATA["meta_schema"]
    meta_schema = open_jsonref(meta_schema)

    # check the parameters
    # 1. whether schema.json file is readable
    # 2. whether $ref in schema.json is extendable
    # 3. whether schema is valid
    # 4. whether properties are duplicated defined
    # 5. whether email is valid
    result = check_parameters(output=output,
                              tz=tz,
                              json_output_filepath=json_output_filepath,
                              schema_url=raw_schema_url,
                              mail=mail,
                              test=test_number,
                              meta_schema=meta_schema,
                              tag="schema")
    
    # if result is false, then there exists mentioned errors
    if not result:
        return result
    
    # if result is true, return
    # output: the json output dictionary
    # schema_dict: the schema json dictionary
    # yaml_dict: the processed schema json dictionary
    output, schema_dict, yaml_dict = result
    
    # subtest 1 - check whether the properties are well documented
    send_message(test_number=test_number,
                 mail=mail,
                 tz=tz,
                 check_type="processing",
                 json_output=None,
                 sub_test_name="Whether properties are well documented")

    output = is_well_documented(output, yaml_dict, data_model_repo_url)
    
    # subtest 2 - check whether the properties are defined in the database
    send_message(test_number=test_number,
                 mail=mail,
                 tz=tz,
                 check_type="processing",
                 json_output=None,
                 sub_test_name="Whether properties are existed in the database")

    output = is_property_already_existed(output, yaml_dict)
    
    # subtest 3 - check whether the metadata is properly reported
    send_message(test_number,
                 mail,
                 tz,
                 check_type="processing",
                 json_output=None,
                 sub_test_name="Metadata part 1 (derivedFrom, license)")

    output = is_metadata_properly_reported(output, schema_dict)
    
    # subtest 4 - check whether the metadata is existent
    send_message(test_number,
                 mail,
                 tz,
                 check_type="processing",
                 json_output=None,
                 sub_test_name="Metadata part 2 ($schema, $id, title, description, modelTags, $schemaVersion, required)"
                 )

    output = is_metadata_existed(output, schema_dict, data_model_repo_url)

    # make a summary of output
    results = schema_output_sum(output)
    output["sumup_results"] = results
    
    if not results["Failed"]:
        customized_json_dumps(output, tz, test_number, json_output_filepath, mail)
        return True
    else:
        # if any of the subtests is failed
        customized_json_dumps(output, tz, test_number, json_output_filepath, mail, flag=False)
        return False


def schema_output_sum(output):
    """
    TODO: import the function from python package by "from pysmartdatamodel.utils import *"
    """

    documentation_status_of_properties = output['documentationStatusOfProperties']
    already_used_properties = output['alreadyUsedProperties']
    available_properties = output['availableProperties']
    metadata = output['metadata']

    results = dict()
    results = {key: [] for key in CHECKED_PROPERTY_CASES}
    results['Failed'] = dict()

    for pp, value in documentation_status_of_properties.items():
        if value['documented'] & value['x-ngsi']:
            results['well documented'].append(pp)
        elif value['x-ngsi'] is False:
            if value['x-ngsi_text'] not in results['Failed'].keys():
                results['Failed'][value['x-ngsi_text']] = []
            results['Failed'][value['x-ngsi_text']].append(pp)
        elif value['documented'] is False:
            if value['text'] not in results['Failed'].keys():
                results['Failed'][value['text']] = []
            results['Failed'][value['text']].append(pp)
        if (pp == "type") and (value["type_specific"] is False):
            results['Failed'][value["type_specific_text"]] = []
            results['Failed'][value["type_specific_text"]].append(pp)
        if 'duplicated_prop' in value:
            try:
                results['Failed'][value['duplicated_prop_text']].append(pp)
            except Exception as e:
                print(e)
                print("Exception in schema_output_sum")
                results['Failed'][value['duplicated_prop_text']] = []
                results['Failed'][value['duplicated_prop_text']].append(pp)

    for pp in already_used_properties:
        # print(pp.keys())
        results['already used'].append(list(pp.keys())[0])

    for pp in available_properties:
        results['newly available'].append(list(pp.keys())[0])

    for pp, value in metadata.items():
        results['Metadata'].append(value['warning'])

    return results






