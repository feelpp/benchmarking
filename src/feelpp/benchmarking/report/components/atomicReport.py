import json, os



class AtomicReport:
    def __init__(self, application_id, machine_id, json_file, possible_test_cases):

        self.data = self.parseJson(json_file)

        self.date = self.data["session_info"]["time_start"]

        self.application_id = application_id
        self.machine_id = machine_id
        self.test_case_id = self.findTestCase(possible_test_cases)

        self.application = None
        self.machine = None
        self.test_case = None

    def setMachine(self, machine):
        self.machine = machine

    def setApplication(self, application):
        self.application = application

    def setTestCase(self, test_case):
        self.test_case = test_case

    def setIndexes(self, application, machine, test_case):
        self.setApplication(application)
        self.setMachine(machine)
        self.setTestCase(test_case)

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

        return test_case

    def filename(self):
        return f"{self.date}"

    def updateData(self, view = "machines"):
        if view == "machines":
            self.data["parent_catalogs"] = f"{self.machine_id}-{self.application_id}-{self.test_case_id}"

        self.data["application_display_name"] = self.application.display_name
        self.data["machine_id"] = self.machine.id
        self.data["machine_display_name"] = self.machine.display_name

    def createReport(self, base_dir, renderer):
        """ Create the report for the atomic report
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
            view (str): The view to use. Default is "machines". Options are "machines" and "applications"
        """

        if base_dir.endswith("machines"):
            output_folder_path = f"{base_dir}/{self.machine_id}/{self.application_id}/{self.test_case_id}"
        elif base_dir.endswith("applications"):
            raise NotImplementedError("Applications view is not implemented yet")
        else:
            raise ValueError("The base_directory must be either 'machines' or 'applications', and must be located under ROOT/pages")

        if not os.path.exists(output_folder_path):
            raise FileNotFoundError(f"The folder {output_folder_path} does not exist. Modules should be initialized beforehand ")

        self.updateData()

        renderer.render(
            f"{output_folder_path}/{self.filename()}.adoc",
            self.data
        )