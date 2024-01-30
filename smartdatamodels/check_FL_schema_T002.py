# FL stands for inside file check for one data model
# this python file is focused on schema.json file

from smartdatamodels.utils import SDMUtils
from smartdatamodels.PC_well_documented import SDMWellDocumented
from smartdatamodels.PC_exist_already import SDMProperties
from smartdatamodels.MD_reported import MDReported
from smartdatamodels.MD_exist import MDExist
from common.config import CONFIG_DATA


class CheckSchema:
    def __init__(self, logger, data_model_repo_url, mail, json_output_filepath, generate_output_file=False):
        self.sdm_properties = SDMProperties(logger=logger)
        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=generate_output_file)
        self.sdm_well_documented = SDMWellDocumented(logger=logger, generate_output_file=generate_output_file)
        self.md_reported = MDReported(logger=logger, generate_output_file=generate_output_file)
        self.md_exist = MDExist(logger=logger, generate_output_file=generate_output_file)

        self.logger = logger
        self.data_model_repo_url = data_model_repo_url
        self.mail = mail
        self.json_output_filepath = json_output_filepath
        self.generate_output_file = generate_output_file

    def check_fl_schema_json(self, test_number, tz):
        """
        Check file schema.json given the data model link
        """
        if self.generate_output_file:
            self.sdm_utils.send_message(test_number, self.mail, tz, check_type="loading")

        output = {"result": False}  # the json answering the test

        raw_schema_url = self.sdm_utils.get_schema_json_raw(self.data_model_repo_url)

        meta_schema = CONFIG_DATA["meta_schema"]
        meta_schema = self.sdm_utils.open_jsonref(meta_schema)

        # check the parameters
        # 1. whether schema.json file is readable
        # 2. whether $ref in schema.json is extendable
        # 3. whether schema is valid
        # 4. whether properties are duplicated defined
        # 5. whether email is valid
        result = self.sdm_utils.check_parameters(output=output,
                                                 tz=tz,
                                                 json_output_filepath=self.json_output_filepath,
                                                 schema_url=raw_schema_url,
                                                 mail=self.mail,
                                                 test=test_number,
                                                 meta_schema=meta_schema,
                                                 tag="Schema")

        # if result is false, then there exists mentioned errors
        if not result:
            return result

        # if result is true, return
        # output: the json output dictionary
        # schema_dict: the schema json dictionary
        # yaml_dict: the processed schema json dictionary
        output, schema_dict, yaml_dict = result

        # subtest 1 - check whether the properties are well documented
        if self.generate_output_file:
            aux = "Whether properties are well documented"
            self.sdm_utils.send_message(test_number=test_number,
                                        mail=self.mail,
                                        tz=tz,
                                        check_type="processing",
                                        json_output=None,
                                        sub_test_name=aux)

        output = self.sdm_well_documented.is_well_documented(output, yaml_dict, self.data_model_repo_url)

        # subtest 2 - check whether the properties are defined in the database
        if self.generate_output_file:
            aux = "Whether properties are existed in the database"
            self.sdm_utils.send_message(test_number=test_number,
                                        mail=self.mail,
                                        tz=tz,
                                        check_type="processing",
                                        json_output=None,
                                        sub_test_name=aux)

        output = self.sdm_properties.is_property_already_existed(output, yaml_dict)

        # subtest 3 - check whether the metadata is properly reported
        if self.generate_output_file:
            aux = "Metadata part 1 (derivedFrom, license)"
            self.sdm_utils.send_message(test_number=test_number,
                                        mail=self.mail,
                                        tz=tz,
                                        check_type="processing",
                                        json_output=None,
                                        sub_test_name=aux)

        output = self.md_reported.is_metadata_properly_reported(output, schema_dict)

        # subtest 4 - check whether the metadata is existent
        if self.generate_output_file:
            aux = "Metadata part 2 ($schema, $id, title, description, modelTags, $schemaVersion, required)"
            self.sdm_utils.send_message(test_number=test_number,
                                        mail=self.mail,
                                        tz=tz,
                                        check_type="processing",
                                        json_output=None,
                                        sub_test_name=aux)

        output = self.md_exist.is_metadata_existed(output, schema_dict, self.data_model_repo_url)

        # make a summary of output
        results = self.schema_output_sum(output)
        output["sumup_results"] = results

        if not results["Failed"]:
            self.sdm_utils.customized_json_dumps(output=output,
                                                 tz=tz,
                                                 test_number=test_number,
                                                 json_output_filepath=self.json_output_filepath,
                                                 mail=self.mail)
            return True
        else:
            # if any of the subtests is failed
            self.sdm_utils.customized_json_dumps(output=output,
                                                 tz=tz,
                                                 test_number=test_number,
                                                 json_output_filepath=self.json_output_filepath,
                                                 mail=self.mail,
                                                 flag=False)
            return False

    def schema_output_sum(self, output):
        """
        TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        """

        documentation_status_of_properties = output['documentationStatusOfProperties']
        already_used_properties = output['alreadyUsedProperties']
        available_properties = output['availableProperties']
        metadata = output['metadata']

        results = dict()
        results = {key: dict() if key == 'Failed' else list() for key in self.sdm_utils.get_check_property_cases()}
        # results = {key: [] for key in CHECKED_PROPERTY_CASES}
        # results['Failed'] = dict()

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






