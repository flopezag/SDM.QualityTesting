# input the root of the data model
# browse directories for .py files
# loading in the masters and execute as a single file
# it has a dictionary with the result of every test

from pytz import timezone
from smartdatamodels.utils import create_output_json, clean_test_data, send_message
from smartdatamodels.check_FS_T001_v1 import check_file_structure
from smartdatamodels.check_FL_schema_T002_v1 import check_fl_schema_json
from smartdatamodels.check_FL_examples_T003_v1 import check_fl_examples
from smartdatamodels.check_FL_others_T004_v1 import check_fl_others
from common.config import CONFIG_DATA


################################################
# Add configuration
# 
# test_dependency: 
#   - key: the current test
#   - value: the tests need to run before running the current test
#  for example:
#       3: [1, 2], means if you wanna run test 3, you have to pass the test 1 and 2
#  
# config_test.json:
#   contains hyperparameters link to metaschema, timezone, starting test number by default
# 
# system parameters:
#   - datamodelRepoUrl: the url to the github repository of a specific data model 
#   - mail: the email address related to the contributor
#   - lasttestnumber: the test that contributor wants to do, 0 by default which means fully test
################################################
class SDMQualityTesting:
    def __init__(self, data_model_repo_url, mail, last_test_number):
        self.number_to_test_name = {
            1: check_file_structure,
            2: check_fl_schema_json,
            3: check_fl_examples,
            4: check_fl_others
        }

        self.test_name_to_number = {
            check_file_structure: 1,
            check_fl_schema_json: 2,
            check_fl_examples: 3,
            check_fl_others: 4
        }

        self.test_dependency = {
            1: [],
            2: [1],
            3: [1, 2],
            4: [1]
        }

        meta_schema = CONFIG_DATA["meta_schema"]
        time_zone = CONFIG_DATA["timezone"]
        self.test_number = CONFIG_DATA["test_number"]

        self.tz = timezone(time_zone)

        ################################################
        # Create output json file for tests
        # assume the system paras are correct
        ################################################
        self.json_output_filepath, output = (
            create_output_json(self.test_number, data_model_repo_url, mail, self.tz, meta_schema)
        )

        ################################################
        # Obtain the tests that need to run based on the given test number from contributor
        # and the previous tests
        ################################################
        self.test_state = dict()
        for key, value in output.items():
            try:
                if int(key) in self.number_to_test_name.keys():
                    self.test_state[key] = value["result"]
            except Exception as e:
                print(e)
                continue

        self.last_test_number = last_test_number
        self.mail = mail
        self.data_model_repo_url = data_model_repo_url

        print(self.test_state)

    def get_need2run_tests(self, test_number, test_state):
        def resolve_dependencies(a_test, the_visited_tests):
            the_visited_tests.add(a_test)
            for dependency in self.test_dependency[a_test]:
                if dependency not in the_visited_tests:
                    resolve_dependencies(dependency, the_visited_tests)

        # Resolve test dependencies and create an ordered list of tests to run
        visited_tests = set()
        if test_number == 0:
            for test in self.test_dependency:
                if test not in visited_tests:
                    resolve_dependencies(test, visited_tests)
        else:
            resolve_dependencies(test_number, visited_tests)

        # print(visited_tests)
        # get the need-to-run tests based on the test_state
        # the first false
        need2run_test = visited_tests.copy()
        for test in visited_tests:
            if str(test) in test_state.keys():
                if not test_state[str(test)]:
                    # clean the json output
                    clean_test_data(self.json_output_filepath, test)
                else:
                    need2run_test.remove(test)

        print(need2run_test)
        ordered_test = [self.number_to_test_name[test] for test in need2run_test]

        return ordered_test

    # get the mapping functions
    def run_tests(self, tests, data_model_repo_url, tz, mail, json_output_filepath):
        # Run the tests in the specified order with the given parameter
        # [# of all tests, # of passed tests, # of failed tests, # of left tests]
        test_stats = [len(tests), 0, 0, len(tests)]
        current_test_state = [True] * len(tests)
        current_test_number = [self.test_name_to_number[test] for test in tests]

        for index, test in enumerate(tests):
            test_number = self.test_name_to_number[test]
            flag = True
            # compare with test dependency
            # current test state
            for dp_test in self.test_dependency[test_number]:
                if (dp_test in current_test_number) and (not current_test_state[current_test_number.index(dp_test)]):
                    flag = False
                    break
            if flag:
                if test(data_model_repo_url, tz, test_number, mail, json_output_filepath):
                    test_stats[1] += 1
                    test_stats[-1] -= 1
                else:
                    current_test_state[index] = False
                    test_stats[2] += 1
                    test_stats[-1] -= 1

        return test_stats

    ################################################
    # Run the tests and send the sum up message
    ################################################
    def do_tests(self):
        test_stats = self.run_tests(tests=self.get_need2run_tests(self.last_test_number, self.test_state),
                                    data_model_repo_url=self.data_model_repo_url,
                                    tz=self.tz,
                                    mail=self.mail,
                                    json_output_filepath=self.json_output_filepath)

        message = (f"{test_stats[0]} tests needed to run, {test_stats[1]} passed, {test_stats[2]} failed, "
                   f"{test_stats[3]} left.\n")

        send_message(test_number=self.test_number,
                     mail=self.mail,
                     tz=self.tz,
                     check_type=message)
