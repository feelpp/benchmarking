import json, os
from feelpp.benchmarking.report.atomicReports.model import AtomicReportModel

class AtomicReport:
    """ Class representing an atomic report. i.e. a report indexed by date, test case, application and machine.
        Holds the data of benchmarks for a specific set of parameters.
        For example, in contains multiple executions with different number of cores, or different input files (but same test case), for a single machine and application.
    """
    def __init__(self, application_id, machine_id, reframe_report_json, plot_config_json,partials_dir):
        """ Constructor for the AtomicReport class
        An atomic report is identified by a single application, machine and test case
        Args:
            application_id (str): The id of the application
            machine_id (str): The id of the machine
            reframe_report_json (str): The path to the reframe report JSON file
            plot_config_json (str): The path to the plot configuration file (usually comes with the reframe report)
            partials_dir (str): The directory path where parametric descriptions of the use case can be found (usually comes with the reframe report). Pass None if non-existent
        """
        data = self.parseJson(reframe_report_json)
        self.plots_config = self.parseJson(plot_config_json)
        self.partials_dir = partials_dir

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

        self.hash_param_map = self.createHashParamMap(data)

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

    def createHashParamMap(self,data):
        hash_param_map = {}
        for run in data["runs"]:
            for testcase in run["testcases"]:
                hash = testcase["hash"]
                hash_param_map[hash] = {"check_params":testcase["check_params"]}

        return hash_param_map

    def movePartials(self,base_dir):
        """ Moves the partial files to a given folder and updates the hashmap
        Args:
            base_dir (str): The base directory where the partials will be moved to
        """
        if not self.partials_dir:
            return

        if not self.hash_param_map:
            raise Exception("hash_param attribute not initialized")

        if not os.path.exists(self.partials_dir):
            raise FileNotFoundError("Parametrized descriptions directory does not exist")

        move_dir = os.path.join(base_dir,self.machine_id,self.application_id,self.use_case_id,self.filename()).replace("-","_").replace(":","_").replace("+","Z")
        if not os.path.exists(move_dir):
            os.makedirs(move_dir)

        for description_filename in os.listdir(self.partials_dir):
            description_file_basename = os.path.basename(description_filename)
            description_file_basename_splitted = description_file_basename.split(".")[0]

            if description_file_basename_splitted in self.hash_param_map:
                os.rename(os.path.join(self.partials_dir,description_filename), os.path.join(move_dir,description_file_basename))
                self.hash_param_map[description_file_basename_splitted]["partial_filepath"] = os.path.join(os.path.relpath(move_dir,start="./docs/modules/ROOT/pages"),description_file_basename)


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

    @staticmethod
    def flatten(nested_json, parent_key=''):
        flat_dict = {}
        for key, value in nested_json.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                flat_dict.update(AtomicReport.flatten(value, new_key))
            else:
                flat_dict[new_key] = value
        return flat_dict

    def parseHashMap(self):
        parsed_hashmap = {}
        for hash, v in self.hash_param_map.items():
            parsed_hashmap[hash] = self.flatten(v["check_params"])
            if "partial_filepath" in v:
                parsed_hashmap[hash]["partial_filepath"] = v["partial_filepath"]

        headers = []
        for entry in parsed_hashmap.values():
            for key in entry.keys():
                if key not in headers:
                    headers.append(key)

        return headers, parsed_hashmap

    def createReport(self, base_dir, renderer):
        """ Create the report for the atomic report
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """
        hash_params_headers, flat_hash_params = self.parseHashMap()
        renderer.render(
            f"{base_dir}/{self.filename()}.adoc",
            dict(
                parent_catalogs = f"{self.application_id}-{self.use_case_id}-{self.machine_id},{self.machine_id}-{self.application_id}-{self.use_case_id},{self.use_case_id}-{self.application_id}-{self.machine_id}",
                application_display_name = self.application.display_name,
                machine_id = self.machine.id, machine_display_name = self.machine.display_name,
                session_info = self.session_info,
                runs = self.runs,
                date = self.date,
                empty = self.empty,
                plots_config = self.plots_config,
                flat_hash_param_map = flat_hash_params,
                hash_params_headers = hash_params_headers
            )
        )


