# property check - PC
# from smartdatamodels.utils import extract_datamodel_from_repo_url
from smartdatamodels.utils import SDMUtils


class SDMWellDocumented:
    def __init__(self, logger, generate_output_file: bool = False):
        self.propertyTypes = ["Property", "Relationship", "GeoProperty"]
        self.incompleteDescription = "Incomplete description"
        self.withoutDescription = "No description at all"
        # doubleDotsDescription = "Double dots in the middle"
        # wrongTypeDescription = "Wrong NGSI types"
        # missingTypeDescription = "Missing NGSI types"
        self.exceptions = ["coordinates", "bbox", "type"]

        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=generate_output_file)

    def parse_yaml_dict(self, yaml_dict, data_model_repo_url, level):
        # TODO: import the function from python package by "from pysmartdatamodel.utils import *"
        attributes = set()

        output = {}
        if isinstance(yaml_dict, list):
            for item in yaml_dict:
                partial_output = self.parse_yaml_dict(item, data_model_repo_url, level + 1)
                output = dict(output, **partial_output)
        else:
            for prop in yaml_dict:
                # print("prop ", prop)

                if prop == "id":
                    continue

                if isinstance(yaml_dict[prop], list) and len(yaml_dict[prop]) > 1 and isinstance(yaml_dict[prop][0], dict):
                    for item in yaml_dict[prop]:
                        partial_output = self.parse_yaml_dict(item, data_model_repo_url, level + 1)
                        output = dict(output, **partial_output)

                if isinstance(yaml_dict[prop], dict):
                    if prop in ["properties", "allOf", "oneOf", "anyOf", "items"]:
                        partial_output = self.parse_yaml_dict(yaml_dict[prop], data_model_repo_url, level + 1)
                        output = dict(output, **partial_output)
                        continue
                    # print("dict prop ", prop)
                    prop_keys = list(yaml_dict[prop].keys())

                    # if there's type, and there's no items, allOf, properties
                    # if type is a
                    if isinstance(yaml_dict[prop], dict) and prop != "x-ngsi" and prop not in self.exceptions:
                        # print("++++ context prop ", prop)

                        try:
                            property_type = yaml_dict[prop]["x-ngsi"]["type"]
                            if property_type in self.propertyTypes:
                                # print(property_type)
                                # print(propertyTypes)
                                output[prop] = {}
                                output[prop]["x-ngsi"] = True
                                output[prop]["x-ngsi_text"] = "ok to " + str(property_type)
                            else:
                                output[prop]["x-ngsi"] = False
                                output[prop]["x-ngsi_text"] = ("Wrong NGSI type of " + property_type +
                                                               " in the description of the property on level "
                                                               + str(level))
                        except Exception as e:
                            print(e)
                            output[prop] = dict()
                            output[prop]["x-ngsi"] = False
                            output[prop]["x-ngsi_text"] = ("Missing NGSI type of " + str(self.propertyTypes)
                                                           + " in the description of the property on level "
                                                           + str(level))

                        # checking the pure description
                        try:
                            description = yaml_dict[prop]["description"]
                            if len(description) > 15:
                                # No double quotes in the middle
                                # if not (".." in description):
                                # If there is a link, check that the link is valid
                                output[prop]["documented"] = True
                                output[prop]["text"] = description
                                # else:
                                #     output[key]["documented"] = False
                                #     output[key]["text"] = doubleDotsDescription
                            else:
                                output[prop]["documented"] = False
                                output[prop]["text"] = self.incompleteDescription
                        except Exception as e:
                            print(e)
                            # output[key] = {}
                            output[prop]["documented"] = False
                            output[prop]["text"] = self.withoutDescription

                        # Type property matches data model name
                        if prop == "type" and level == 1:
                            try:
                                property_type = yaml_dict[prop]["enum"]
                                if (property_type[0] ==
                                        self.sdm_utils.extract_datamodel_from_repo_url(data_model_repo_url)):
                                    output[prop]["type_specific"] = True
                                    output[prop]["type_specific_text"] = (
                                            "Type property matches to data model name on level " + str(level))
                                else:
                                    output[prop]["type_specific"] = False
                                    output[prop]["type_specific_text"] = (
                                            "Type property doesn't match to data model name on level " + str(level))
                            except Exception as e:
                                print(e)
                                output[prop]["type_specific"] = False
                                output[prop]["type_specific_text"] = "Missing Type property"

                        # duplicated attributes
                        if prop in attributes:
                            output[prop]["duplicated_prop"] = True
                            output[prop]["duplicated_prop_text"] = (
                                    "Duplicated prop " + str(prop) + " on level " + str(level))
                        else:
                            attributes.add(prop)

                    if "properties" in prop_keys:
                        partial_output = self.parse_yaml_dict(yaml_dict[prop]["properties"], data_model_repo_url, level + 1)
                        output = dict(output, **partial_output)
                    if "items" in prop_keys and yaml_dict[prop]["items"]:
                        if isinstance(yaml_dict[prop]["items"], list):
                            for index in range(len(yaml_dict[prop]["items"])):
                                partial_output = (
                                    self.parse_yaml_dict(yaml_dict[prop]["items"][index], data_model_repo_url, level + 1))
                                output = dict(output, **partial_output)
                        else:
                            partial_output = self.parse_yaml_dict(yaml_dict[prop]["items"], data_model_repo_url, level + 1)
                            output = dict(output, **partial_output)
                    if "anyOf" in prop_keys:
                        partial_output = self.parse_yaml_dict(yaml_dict[prop]["anyOf"], data_model_repo_url, level + 1)
                        output = dict(output, **partial_output)
                    if "allOf" in prop_keys:
                        partial_output = self.parse_yaml_dict(yaml_dict[prop]["allOf"], data_model_repo_url, level + 1)
                        output = dict(output, **partial_output)
                    if "oneOf" in prop_keys:
                        partial_output = self.parse_yaml_dict(yaml_dict[prop]["oneOf"], data_model_repo_url, level + 1)
                        output = dict(output, **partial_output)

        return output

    def is_well_documented(self, output, yaml_dict, data_model_repo_url):
        """
        Make summary for yamlDict
        """
        documented = "documentationStatusOfProperties"
        # echo("yamlDict", yamlDict)
        # output[documented] = {}
        output[documented] = self.parse_yaml_dict(yaml_dict, data_model_repo_url, 1)

        # for key in yamlDict:
        #     # print(key)
        #     # print(yamlDict[key])
        #     ################### warning ###################
        #     # this will fail wit any attribute defined through a oneOf, allOf or anyOf
        #     ################### warning ###################

        #     if key != "id":  # this will
        #         try:
        #             propertyType = yamlDict[key]["x-ngsi"]["type"]
        #             if propertyType in propertyTypes:
        #                 # print(propertyType)
        #                 # print(propertyTypes)
        #                 output[documented][key] = {}
        #                 output[documented][key]["x-ngsi"] = True
        #                 output[documented][key]["x-ngsi_text"] = "ok to " + str(propertyType)
        #             else:
        #                 output[documented][key]["x-ngsi"] = False
        #                 output[documented][key]["x-ngsi_text"] =
        #                       "Wrong NGSI type of " + propertyType + " in the description of the property"
        #         except:
        #             output[documented][key] = {}
        #             output[documented][key]["x-ngsi"] = False
        #             output[documented][key]["x-ngsi_text"] =
        #                   "Missing NGSI type of " + str(propertyTypes) + " in the description of the property"

        #         # checking the pure description
        #         try:
        #             description = yamlDict[key]["description"]
        #             if len(description) > 15:
        #                 # No double quotes in the middle
        #                 # if not (".." in description):
        #                     # If there is a link, check that the link is valid
        #                 output[documented][key]["documented"] = True
        #                 output[documented][key]["text"] = description
        #                 # else:
        #                 #     output[documented][key]["documented"] = False
        #                 #     output[documented][key]["text"] = doubleDotsDescription
        #             else:
        #                 output[documented][key]["documented"] = False
        #                 output[documented][key]["text"] = incompleteDescription
        #         except:
        #             # output[documented][key] = {}
        #             output[documented][key]["documented"] = False
        #             output[documented][key]["text"] = withoutDescription

        #    # Type property matches data model name
        #    if key == "type":
        #       try:
        #         propertyType = yamlDict[key]["enum"]
        #         if propertyType[0] == extract_data_model_from_repoUrl(data_model_repo_url):
        #             output[documented][key]["type_specific"] = True
        #             output[documented][key]["type_specific_text"] = "Type property matches to data model name"
        #         else:
        #             output[documented][key]["type_specific"] = False
        #             output[documented][key]["type_specific_text"] = "Type property doesn't match to data model name"
        #     except:
        #         output[documented][key]["type_specific"] = False
        #         output[documented][key]["type_specific_text"] = "Missing Type property"

        all_properties = 0
        documented_properties = 0
        faulty_description_properties = 0
        not_described_properties = 0
        for key in output[documented]:
            all_properties += 1
            # print(output["properties"][key]["documented"])
            if output[documented][key]["documented"]:
                documented_properties += 1
            elif output[documented][key]["text"] == self.incompleteDescription:
                faulty_description_properties += 1
            elif output[documented][key]["text"] == self.withoutDescription:
                not_described_properties += 1

        output["schemaDiagnose"] = ("This schema has " + str(all_properties) + " properties. "
                                    + str(not_described_properties) + " properties are not described at all and "
                                    + str(faulty_description_properties) + " have descriptions that must be completed. "
                                    + str(all_properties - faulty_description_properties - not_described_properties)
                                    + " are described but you can review them anyway. ")

        return output
