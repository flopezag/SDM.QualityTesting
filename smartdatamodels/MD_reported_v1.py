# Check whether the metadata is properly reported in schema.json

from validator_collection import checkers
from smartdatamodels.utils import is_url_existed
# TODO: import the function from python package by "from pysmartdatamodel.utils import *"


def is_metadata_properly_reported(output, schema_dict):
    try:
        metadata = "metadata"
        output[metadata] = {}
        if "derived_from" in schema_dict:
            derived_from = schema_dict["derivedFrom"]
            if derived_from != "":
                # check that it is a valid url
                if not checkers.is_url(derived_from):
                    output["metadata"]["derivedFrom"] = {"warning": "derived_from is not a valid url"}
                else:
                    if not is_url_existed(derived_from)[0]:
                        output["metadata"]["derivedFrom"] = {"warning": "derived_from url is not reachable"}
        else:
            output["metadata"]["derivedFrom"] = \
                {"warning": "not derived_from clause, include derived_from = '' in the header"}
    except Exception as e:
        print(e)
        output["metadata"]["derivedFrom"] = \
            {"warning": "not possible to check derived_from clause, "
                        "Does it exist a derived_from = '' clause in the header?"}

    # check that the header license is properly reported
    try:
        metadata = "metadata"
        if "metadata" not in output:
            output[metadata] = {}
        if "license" in schema_dict:
            data_model_license = schema_dict["license"]
            if data_model_license != "":
                # check that it is a valid url
                if not checkers.is_url(data_model_license):
                    output["metadata"]["license"] = \
                        {"warning": "License is not a valid url. It should be a link to the license document"}
                else:
                    if not is_url_existed(data_model_license)[0]:
                        output["metadata"]["license"] = \
                            {"warning": "license url is not reachable"}
            else:
                output["metadata"]["license"] = \
                    {"warning": "license is empty, include a license = '' in the header "}
        else:
            output["metadata"]["license"] = \
                {"warning": "not license clause, does it exist a license = '' in the header?"}
    except Exception as e:
        print(e)
        output["metadata"]["license"] = \
            {"warning": "not possible to check license clause"}

    return output
