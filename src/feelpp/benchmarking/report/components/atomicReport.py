import json, os
from feelpp.benchmarking.report.components.models import AtomicReportModel

class AtomicReport:
    """ Class representing an atomic report. i.e. a report indexed by date, test case, application and machine.
        Holds the data of benchmarks for a specific set of parameters.
        For example, in contains multiple executions with different number of cores, or different input files (but same test case), for a single machine and application.
    """
    def __init__(self, application_id, machine_id, reframe_report_json, plot_config_json):
        """ Constructor for the AtomicReport class
        An atomic report is identified by a single application, machine and test case
        Args:
            application_id (str): The id of the application
            machine_id (str): The id of the machine
            reframe_report_json (str): The path to the reframe report JSON file
            plot_config_json (str): The path to the plot configuration file (usually comes with the reframe report)
        """
        data = self.parseJson(reframe_report_json)
        self.plots_config = self.parseJson(plot_config_json)

        self.filepath = reframe_report_json
        self.session_info = data["session_info"]
        self.runs = data["runs"]
        self.date = data["session_info"]["time_start"]

        self.application_id = application_id
        self.machine_id = machine_id
        self.use_case_id = self.findUseCase(data)

        self.application = None
        self.machine = None
        self.use_case = None

        self.empty = all(testcase["perfvars"]==None for run in data["runs"] for testcase in run["testcases"])

        self.model = AtomicReportModel(self.runs)

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

    def parseJson(self,file_path):
        """ Load a json file
        Args:
            file_path (str): The JSON file to parse
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def findUseCase(self,data):
        """ Find the test case of the report
        """
        use_case = data["runs"][0]["testcases"][0]["check_vars"]["use_case"]
        assert all( testcase["check_vars"]["use_case"] == use_case for run in data["runs"] for testcase in run["testcases"]), "useCase differ from one testcase to another"
        return use_case

    def filename(self):
        """ Build the filename for the report
        Returns:
            str: The filename
        """
        return f"{self.date}"

    def createReport(self, base_dir, renderer):
        """ Create the report for the atomic report
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """

        output_folder_path = f"{base_dir}/{self.application_id}/{self.use_case_id}/{self.machine_id}"

        if not os.path.exists(output_folder_path):
            raise FileNotFoundError(f"The folder {output_folder_path} does not exist. Modules should be initialized beforehand ")

        renderer.render(
            f"{output_folder_path}/{self.filename()}.adoc",
            dict(
                parent_catalogs = f"{self.application_id}-{self.use_case_id}-{self.machine_id}",
                application_display_name = self.application.display_name,
                machine_id = self.machine.id, machine_display_name = self.machine.display_name,
                session_info = self.session_info,
                runs = self.runs,
                date = self.date,
                empty = self.empty,
                plots_config = self.plots_config
            )
        )


