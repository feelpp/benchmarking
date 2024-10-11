import json, os
from feelpp.benchmarking.report.components.figureFactory import FigureFactory
from feelpp.benchmarking.reframe.config.configSchemas import Plot
import numpy as np
import pandas as pd


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


class AtomicReportController:
    """ Controller component of the Atomic Report, it orchestrates the model with the view"""
    def __init__(self, model, view):
        """
        Args:
            model (AtomicReportModel): The atomic report model component
            view (AtomicReportView): The atomic report view component
        """
        self.model = model
        self.view = view

    def generateAll(self):
        """ Creates plotly figures for each plot specified on the view config file
        Returns a list of plotly figures.
        """
        for plot_config in self.view.plots_config:
            for plot in FigureFactory.create(plot_config):
                yield plot.createFigure(self.model.master_df)


class AtomicReportModel:
    """Model component for the atomic report """
    def __init__(self, runs):
        """ Extracts the dimensions of the tests and builds a master df used by other classes"""
        self.master_df = self.buildMasterDf(runs)

    def buildMasterDf(self,runs):
        """Build a dataframe where each row is indexed by a perfvar and its respective values
        Args:
            runs list[dict]: The reframe runs with testcases
        returns
            pd.DataFrame: The master dataframe
        """
        processed_data = []

        for i,testcase in enumerate(runs[0]["testcases"]): #TODO: support multiple runs
            if not testcase["perfvars"]:
                tmp_dct = {
                    "testcase_i" :i,
                    "performance_variable": "",
                    "value": None,
                    "unit": "",
                    "reference": None,
                    "thres_lower": None,
                    "thres_upper": None,
                    "status": None,
                    "absolute_error": None,
                    "testcase_time_run": testcase["time_run"],
                }
                for dim, v in testcase["check_params"].items():
                    tmp_dct[dim] = v
                processed_data.append(tmp_dct)
                continue

            for perfvar in testcase["perfvars"]:
                tmp_dct = {}
                tmp_dct["testcase_i"] = i
                tmp_dct["performance_variable"] = perfvar["name"]
                tmp_dct["value"] = float(perfvar["value"])
                tmp_dct["unit"] = perfvar["unit"]
                tmp_dct["reference"] = float(perfvar["reference"]) if perfvar["reference"] else np.nan
                tmp_dct["thres_lower"] = float(perfvar["thres_lower"]) if perfvar["thres_lower"] else np.nan
                tmp_dct["thres_upper"] = float(perfvar["thres_upper"]) if perfvar["thres_upper"] else np.nan
                tmp_dct["status"] = tmp_dct["thres_lower"] <= tmp_dct["value"] <= tmp_dct["thres_upper"] if not np.isnan(tmp_dct["thres_lower"]) and not np.isnan(tmp_dct["thres_upper"]) else np.nan
                tmp_dct["absolute_error"] = np.abs(tmp_dct["value"] - tmp_dct["reference"])
                tmp_dct["testcase_time_run"] = testcase["time_run"]

                for dim, v in testcase["check_params"].items():
                    tmp_dct[dim] = v

                processed_data.append(tmp_dct)

        return pd.DataFrame(processed_data)

class AtomicReportView:
    """ View component for the Atomic Report, it contains all figure generation related code """
    def __init__(self,plots_config):
        """ Parses the plots config list. This JSON tells what plots to show and how to display them
        Args:
            plots_config list[dict]. List with dictionaries specifying plots configuration.
        """
        self.plots_config = [Plot(**d) for d in plots_config]
