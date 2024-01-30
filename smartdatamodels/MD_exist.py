# Check whether the metadata exists in schema.json and examples
# schema.json: $id, title, $schema, $schemaVersion, modelTag, description, required
# id, type, @context
#from smartdatamodels.utils import (extract_datamodel_from_repo_url, is_url_existed, KEYWORDS_FOR_CERTAIN_CHECK,
#                                   get_context_jsonld_raw, create_schema_json_url)
from smartdatamodels.utils import SDMUtils


class MDExist:
    def __init__(self, logger, generate_output_file):
        self.logger = logger

        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=generate_output_file)

        self.metadata_check = {
            "id": lambda output, json_dict, repo_url: self.check_id(output, json_dict),
            "type": lambda output, json_dict, repo_url: self.check_type(output, json_dict, repo_url),
            "@context": lambda output, json_dict, repo_url: self.check_at_context(output, json_dict, repo_url),
        }

    ################################################
    # Metadata in examples: id, type, @context
    ################################################
    @staticmethod
    def check_id(output, json_dict):
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "id" in json_dict:
                metadata_id = json_dict["id"]
                if metadata_id == "":
                    output["metadata"]["id"] = {"warning": "id is empty"}
                elif not isinstance(metadata_id, str):
                    output["metadata"]["id"] = {"warning": "id is not a string"}
            else:
                output["metadata"]["id"] = {"warning": "Missing id clause, include id = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["id"] = \
                {"warning": "not possible to check id clause, Does it exist a id = '' in the header?"}

        return output

    def check_type(self, output, json_dict, repo_url):
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "type" in json_dict:
                data_model_type = json_dict["type"]
                if data_model_type == "":
                    output["metadata"]["type"] = {"warning": "type is empty"}
                elif not isinstance(data_model_type, str):
                    output["metadata"]["type"] = {"warning": "type is not a string"}
                elif data_model_type != self.sdm_utils.extract_datamodel_from_repo_url(repo_url):
                    output["metadata"]["type"] = \
                        {"warning": f"type {data_model_type} doesn't match the data model "
                                    f"{self.sdm_utils.extract_datamodel_from_repo_url(repo_url)}, please check it again"}
            else:
                output["metadata"]["type"] = \
                    {"warning": "Missing type clause, include type = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["type"] = \
                {"warning": "not possible to check type clause, Does it exist a type = '' in the header?"}

        return output

    def check_at_context(self, output, json_dict, repo_url):
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "@context" in json_dict:
                context = json_dict["@context"]
                if len(context) == 0:
                    output["metadata"]["@context"] = \
                        {"warning": "@context is an empty list or is empty"}
                else:
                    for url in context:
                        if not self.sdm_utils.is_url_existed(url)[0]:
                            output["metadata"]["@context"] = \
                                {"warning": f"{url} in @context is not reachable, please check it again"}
                if ((self.sdm_utils.KEYWORDS_FOR_CERTAIN_CHECK in repo_url) and
                        ("@context" not in output["metadata"].keys())):
                    if not (self.sdm_utils.get_context_jsonld_raw(repo_url) in context):
                        output["metadata"]["@context"] = \
                            {"warning": "@context doesn't include the right context link, please check it again "
                                        "or ignore this message if it's an unpublished datamodel"}
            else:
                output["metadata"]["@context"] = \
                    {"warning": "Missing @context clause, include @context = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["@context"] = \
                {"warning": "not possible to check @context clause, Does it exist a @context = '' in the header?"}

        return output

    def is_metadata_existed_examples(self, output, json_dict, repo_url, checklist=None):
        # check "id", "type", "@context"
        if not checklist:
            checklist = ["id", "type", "@context"]

        for checkpoint in checklist:
            if checkpoint in self.metadata_check:
                check_func = self.metadata_check[checkpoint]
                output = check_func(output, json_dict, repo_url)

        return output

    ################################################
    # Metadata in examples: id, type, @context
    ################################################
    # TODO: import the function from python package by "from pysmartdatamodel.utils import *"
    def is_metadata_existed(self, output, json_dict, repo_url):

        # if checkall is True, then ignore checklist
        # if checkall is False, then checklist will be used

        # if not checkall:
        #   ["$schema", "$id", "title", "", "description", "tags", "version", "required clause"]

        # check that the "$schema" exist, by default is "http://json-schema.org/schema"
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "$schema" in json_dict:
                schema = json_dict["$schema"]
                if schema == "":
                    output["metadata"]["$schema"] = {"warning": "$schema is empty"}

                elif not isinstance(schema, str):
                    output["metadata"]["$schema"] = {"warning": "$schema is not a string"}

                elif schema != "http://json-schema.org/schema#":
                    output["metadata"]["$schema"] = \
                        {"warning": "$schema should be \"http://json-schema.org/schema#\" by default"}
            else:
                output["metadata"]["$schema"] = \
                    {"warning": "Missing $schema clause, include $schema = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["$schema"] = \
                {"warning": "not possible to check $schema clause, Does it exist a $schema = '' in the header?"}

        # check that the "$id" exist
        try:
            # print(jsonDict)
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "$id" in json_dict:
                # print("-----------")
                metadata_id = json_dict["$id"]
                if metadata_id == "":
                    output["metadata"]["$id"] = {"warning": "$id is empty"}
                elif not isinstance(metadata_id, str):
                    output["metadata"]["$id"] = {"warning": "$id is not a string"}
                # https://smart-data-models.github.io/dataModel.DataQuality/DataQualityAssessment/schema.json
                elif ((self.sdm_utils.KEYWORDS_FOR_CERTAIN_CHECK in repo_url) and
                      (metadata_id != self.sdm_utils.create_schema_json_url(repo_url))):
                    output["metadata"]["$id"] = \
                        {"warning": "$id doesn't match, please check it again or ignore this message if it's an "
                                    "unpublished data model"}
            else:
                output["metadata"]["$id"] = \
                    {"warning": "Missing $id clause, include $id = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["$id"] = \
                {"warning": "not possible to check $id clause, Does it exist a $id = '' in the header?"}

        # check that the title exist
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = dict()

            if "title" in json_dict:
                title = json_dict["title"]
                if title == "":
                    output["metadata"]["title"] = {"warning": "Title is empty"}
                elif not isinstance(title, str):
                    output["metadata"]["title"] = {"warning": "Title is not a string"}
                elif len(title) < 15:
                    output["metadata"]["title"] = {"warning": "Title too short"}
            else:
                output["metadata"]["title"] = {"warning": "Missing title clause, include title = '' in the header"}
                title = None

        except Exception as e:
            print(e)
            output["metadata"]["title"] = \
                {"warning": "not possible to check title clause, Does it exist a title = '' in the header?"}
            title = None

        # check that the description exists
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "description" in json_dict:
                description = json_dict["description"]
                if description == "":
                    output["metadata"]["description"] = {"warning": "Description is empty"}
                elif not isinstance(description, str):
                    output["metadata"]["description"] = {"warning": "Description is not a string"}
                elif len(description) < 34:
                    output["metadata"]["description"] = {"warning": "Description is too short"}
            else:
                output["metadata"]["description"] = \
                    {"warning": "Missing description clause, include description = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["description"] = \
                {"warning": "not possible to check description clause, does it exist a description = '' in the header?"}

        # check that the tags exist
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "modelTags" in json_dict:
                model_tags = json_dict["modelTags"]
                if model_tags == "":
                    output["metadata"]["modelTags"] = {"warning": "modelTags is empty"}
                elif not isinstance(title, str):
                    output["metadata"]["modelTags"] = {"warning": "modelTags is not a string"}
            else:
                output["metadata"]["modelTags"] = \
                    {"warning": "Missing modelTags clause, , include modelTags = '' in the header"}
        except Exception as e:
            print(e)
            output["metadata"]["modelTags"] = \
                {"warning": "not possible to check modelTags clause, does it exit a modelTags = '' in the header?"}

        # check that the version exists
        try:
            import re
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "$schemaVersion" in json_dict:
                schema_version = json_dict["$schemaVersion"]
                pattern = r"^\d{1,3}.\d{1,3}.\d{1,3}$"
                if schema_version == "":
                    output["metadata"]["schemaVersion"] = \
                        {"warning": "missing $schemaVersion, include the value. Default = 0.0.1"}
                elif not isinstance(schema_version, str):
                    output["metadata"]["schemaVersion"] = {"warning": "$schemaVersion is not a string"}
                elif re.search(pattern, schema_version) is None:
                    output["metadata"]["schemaVersion"] = {"warning": "Schema version format wrong. Right is x.x.x"}
            else:
                output["metadata"]["schemaVersion"] = \
                    {"warning": "Missing schemaVersion clause, include $schemaVersion = '' in the header "}
        except Exception as e:
            print(e)
            output["metadata"]["schemaVersion"] = \
                {"warning": "not possible to check schemaVersion clause, "
                            "does it exist a $schemaVersion = '' in the header?"}

        # check that the required clause exists
        try:
            metadata = "metadata"
            if "metadata" not in output:
                output[metadata] = {}
            if "required" in json_dict:
                required = json_dict["required"]
                # print(required)
                # print(type(required))
                if required == "":
                    output["metadata"]["required"] = \
                        {"warning": "missing required, include the values. Default = ['id', 'type]"}
                elif not isinstance(required, list):
                    output["metadata"]["required"] = {"warning": "required is not a list"}
                elif ("id" not in required) or ("type" not in required):
                    output["metadata"]["required"] = {"warning": "id and type are mandatory"}
                elif len(required) > 4:
                    output["metadata"]["required"] = \
                        {"warning": "Too many required attributes, "
                                    "consider its reduction to less than 5 preferably just id and type"}
            else:
                output["metadata"]["required"] = {"warning": "Missing required clause, include required = ['id', 'type']"}
        except Exception as e:
            print(e)
            output["metadata"]["required"] = \
                {"warning": "not possible to check required clause, does it exist a required = ['id', 'type']?"}

        return output
