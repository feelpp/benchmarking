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
        self.data = self.parseJson(reframe_report_json)

        self.data["plots_config_filepath"] = plot_config_json

        self.date = self.data["session_info"]["time_start"]

        self.application_id = application_id
        self.machine_id = machine_id
        self.use_case_id = self.findUseCase()

        self.application = None
        self.machine = None
        self.use_case = None

        self.data["empty"] = all(testcase["perfvars"]==None for run in self.data["runs"] for testcase in run["testcases"])

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

    def findUseCase(self):
        """ Find the test case of the report
        """
        use_case = self.data["runs"][0]["testcases"][0]["check_vars"]["use_case"]
        assert all( testcase["check_vars"]["use_case"] == use_case for run in self.data["runs"] for testcase in run["testcases"]), "useCase differ from one testcase to another"
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
        #TODO: Can be a generator
        figs = []
        for plot_config in self.view.plots_config:
            for plot in FigureFactory.create(plot_config):
                figs.append(plot.createFigure(self.model.master_df))
        return figs


class AtomicReportModel:
    """Model component for the atomic report """
    def __init__(self, file_path):
        """ Parses the JSON data, extracts the dimensions of the tests and builds a master df used by other classes"""
        self.buildMasterDf( self.parseJson(file_path) )

    def parseJson(self, file_path):
        """ Load a json file
        Args:
            file_path (str): The JSON file to parse
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data


    def buildMasterDf(self,data):
        """Build a dataframe where each row is indexed by a perfvar and its respective values
        Args:
            data (dict): The parsed JSON data
        """
        processed_data = []

        for i,testcase in enumerate(data["runs"][0]["testcases"]): #TODO: support multiple runs
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
                    "time_start":data["session_info"]["time_start"],
                    "time_end":data["session_info"]["time_end"]
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
                tmp_dct["time_start"] = pd.to_datetime(data["session_info"]["time_start"])
                tmp_dct["time_end"] = pd.to_datetime(data["session_info"]["time_end"])

                for dim, v in testcase["check_params"].items():
                    tmp_dct[dim] = v

                processed_data.append(tmp_dct)

        self.master_df = pd.DataFrame(processed_data)

class AtomicReportView:
    """ View component for the Atomic Report, it contains all figure generation related code """
    def __init__(self,plots_config_path):
        """ Opens and parses the plots config file. This file tells what plots to show and how to display them"""
        with open(plots_config_path, 'r') as file:
            data = json.load(file)
        self.plots_config = [Plot(**d) for d in data]
