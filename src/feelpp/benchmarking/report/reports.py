from feelpp.benchmarking.report.renderer import Renderer
import json



class AtomicReport:
    def __init__(self, application_id, machine_id, json_file, possible_test_cases):

        self.data = self.parseJson(json_file)

        self.date = self.data["session_info"]["time_start"]

        self.application_id = application_id
        self.machine_id = machine_id
        self.test_case_id = self.findTestCase(possible_test_cases)

        self.applications = None
        self.machines = None
        self.test_case = None

    def setIndexes(self, application, machine, test_case):
        self.applications = application
        self.machines = machine
        self.test_case = test_case

    def parseJson(self, input_json):
        """ Parse the JSON file to add or modify some fields
        Args:
            input_json (str): The path to the JSON file
        Returns:
            dict: The parsed JSON file
        """
        with open(input_json, 'r') as file:
            data = json.load(file)

        data['filepath'] = input_json

        return data

    def findTestCase(self, possible_test_cases):
        """ Find the test case of the report
        Args:
            possible_test_cases (list): The possible test cases that can be found.
                                        Only the first found will be set
        """
        test_case = "default"
        if len(self.data["runs"]) == 0 or len(self.data["runs"][0]["testcases"]) == 0:
            return test_case

        for test_case in possible_test_cases:
            if test_case in self.data["runs"][0]["testcases"][0]["tags"]:
                return test_case

