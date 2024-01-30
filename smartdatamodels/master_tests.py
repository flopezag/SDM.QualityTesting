# input the root of the data model
# browse directories for .py files
# loading in the masters and execute as a single file
# it has a dictionary with the result of every test

from pytz import timezone
from smartdatamodels.utils import SDMUtils
from smartdatamodels.check_FL_schema_T002 import CheckSchema
from smartdatamodels.check_FS_T001 import CheckStructure
from smartdatamodels.check_FL_examples_T003 import CheckExamples
from smartdatamodels.check_FL_others_T004 import CheckOtherFiles
from common.config import CONFIG_DATA


################################################
# Add configuration
# 
# test_dependency: 
#   - key: the current test
#   - value: the tests need to run before running the current test
#  for example:
#       3: [1, 2], means if you want to run test 3, you have to pass the test 1 and 2
#  
# config_test.json:
#   contains hyperparameters link to metaschema, timezone, starting test number by default
# 
# system parameters:
#   - data_model_repo_url: the url to the GitHub repository of a specific data model
#   - mail: the email address related to the contributor
#   - last_test_number: the test that contributor wants to do, 0 by default which means fully test
################################################
class SDMQualityTesting:
    def __init__(self, data_model_repo_url, mail, last_test_number, logger):
        meta_schema = CONFIG_DATA["meta_schema"]
        time_zone = CONFIG_DATA["timezone"]
        self.test_number = CONFIG_DATA["test_number"]
        self.generate_output_file = CONFIG_DATA["generate_output_file"]

        self.logger = logger
        self.tz = timezone(time_zone)

        self.sdm_utils = SDMUtils(logger=logger, generate_output_file=self.generate_output_file)

        ################################################
        # Create output json file for tests
        # assume the system paras are correct
        ################################################
        self.json_output_filepath, self.output = (
            self.sdm_utils.create_output_json(self.test_number, data_model_repo_url, mail, self.tz, meta_schema)
        )

        check_fl_schema_json = CheckSchema(logger=logger,
                                           data_model_repo_url=data_model_repo_url,
                                           mail=mail,
                                           json_output_filepath=self.json_output_filepath,
                                           generate_output_file=self.generate_output_file).check_fl_schema_json

        check_file_structure = CheckStructure(logger=logger,
                                              data_model_repo_url=data_model_repo_url,
                                              mail=mail,
                                              json_output_filepath=self.json_output_filepath,
                                              generate_output_file=self.generate_output_file).check_file_structure

        check_fl_examples = CheckExamples(logger=logger,
                                          data_model_repo_url=data_model_repo_url,
                                          mail=mail,
                                          json_output_filepath=self.json_output_filepath,
                                          generate_output_file=self.generate_output_file).check_fl_examples

        check_fl_others = CheckOtherFiles(logger=logger,
                                          data_model_repo_url=data_model_repo_url,
                                          mail=mail,
                                          json_output_filepath=self.json_output_filepath,
                                          generate_output_file=self.generate_output_file).check_fl_others

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

        ################################################
        # Obtain the tests that need to run based on the given test number from contributor
        # and the previous tests
        ################################################
        self.test_state = dict()
        keys_to_search = [str(x) for x in list(self.test_dependency.keys())]
        for key in keys_to_search:
            try:
                self.test_state[key] = self.output[key]["result"]
            except KeyError:
                self.test_state[key] = False

        self.last_test_number = last_test_number
        self.mail = mail
        self.data_model_repo_url = data_model_repo_url

        self.logger.info(f"Test state values: '{self.test_state}'")

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
                    self.sdm_utils.clean_test_data(self.json_output_filepath, test, self.logger)
                else:
                    need2run_test.remove(test)

        self.logger.info(f"Tests need to run: '{need2run_test}'")

        ordered_test = [self.number_to_test_name[test] for test in need2run_test]

        return ordered_test

    # get the mapping functions
    def run_tests(self, tests, tz):
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
                result, aux = test(tz=tz, test_number=test_number)
                self.output[str(test_number)] = aux
                if result:
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
                                    tz=self.tz)

        if self.generate_output_file:
            message = (f"{test_stats[0]} tests needed to run, {test_stats[1]} passed, {test_stats[2]} failed, "
                       f"{test_stats[3]} left.\n")

            self.sdm_utils.send_message(test_number=self.test_number,
                                        mail=self.mail,
                                        tz=self.tz,
                                        check_type=message)

        return self.output
