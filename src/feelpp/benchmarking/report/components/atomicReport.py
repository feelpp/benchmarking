import json, os

class AtomicReport:
    """ Class representing an atomic report. i.e. a report indexed by date, test case, application and machine.
        Holds the data of benchmarks for a specific set of parameters.
        For example, in contains multiple executions with different number of cores, or different input files (but same test case), for a single machine and application.
    """
    def __init__(self, application_id, machine_id, json_file, possible_use_cases):
        """ Constructor for the AtomicReport class
        An atomic report is identified by a single application, machine and test case
        Args:
            application_id (str): The id of the application
            machine_id (str): The id of the machine
            json_file (str): The path to the JSON file
            possible_use_cases (list): The possible test cases that can be found.
                                        Only the first found will be set
        """
        self.data = self.parseJson(json_file)

        self.date = self.data["session_info"]["time_start"]

        self.application_id = application_id
        self.machine_id = machine_id
        self.use_case_id = self.findUseCase(possible_use_cases)

        self.application = None
        self.machine = None
        self.use_case = None

    def setIndexes(self, application, machine, use_case):
        """ Set the indexes for the atomic report.
        Along with the date, they should form a unique identifier for the report.
        Args:
            application (Application): The application
            machine (Machine): The machine
            use_case (UseCase): The test case
        """
        self.machine = machine
        self.application = application
        self.use_case = use_case

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

    def findUseCase(self, possible_use_cases):
        """ Find the test case of the report
        Args:
            possible_use_cases (list): The possible test cases that can be found.
                                        Only the first found will be set
        """
        use_case = "default"
        if len(self.data["runs"]) == 0 or len(self.data["runs"][0]["testcases"]) == 0:
            return use_case

        for use_case in possible_use_cases:
            if use_case in self.data["runs"][0]["testcases"][0]["tags"]:
                return use_case

        return use_case

    def filename(self):
        """ Build the filename for the report
        Returns:
            str: The filename
        """
        return f"{self.date}"

    def updateData(self, view = "machines"):
        """ Update the data attribute to be rendered in the report, depending on the set parameters
        Args:
            view (str): Whether to render as machines>apps or apps>machines. Default is "machines". Options are "machines" and "applications"
        """
        if view == "machines":
            self.data["parent_catalogs"] = f"{self.machine_id}-{self.application_id}-{self.use_case_id}"
        elif view == "applications":
            self.data["parent_catalogs"] = f"{self.application_id}-{self.use_case_id}-{self.machine_id}"

        self.data["application_display_name"] = self.application.display_name
        self.data["machine_id"] = self.machine.id
        self.data["machine_display_name"] = self.machine.display_name

    def createReport(self, base_dir, renderer):
        """ Create the report for the atomic report
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """

        if base_dir.endswith("machines"):
            output_folder_path = f"{base_dir}/{self.machine_id}/{self.application_id}/{self.use_case_id}"
            self.updateData("machines")
        elif base_dir.endswith("applications"):
            output_folder_path = f"{base_dir}/{self.application_id}/{self.use_case_id}/{self.machine_id}"
            self.updateData("applications")
        else:
            raise ValueError("The base_directory must be either 'machines' or 'applications', and must be located under ROOT/pages")

        if not os.path.exists(output_folder_path):
            raise FileNotFoundError(f"The folder {output_folder_path} does not exist. Modules should be initialized beforehand ")


        renderer.render(
            f"{output_folder_path}/{self.filename()}.adoc",
            self.data
        )