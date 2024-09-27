import json, os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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


class AtomicReportModel:
    """Model component for the atomic report """
    def __init__(self, file_path):
        """ Parses the JSON data, extracts the dimensions of the tests and builds a master df used by other classes"""
        data = self.parseJson(file_path)

        self.extractDimensions(data)
        self.buildMasterDf(data)

    def parseJson(self, file_path):
        """ Load a json file
        Args:
            file_path (str): The JSON file to parse
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
            data = data["runs"][0] #TODO: support multiple runs

        return data

    def extractDimensions(self,data):
        """Get the check_params object keys from the first testcase.
        Check that the rest of the cases have the same fields
        Args:
            Data (dict): The loaded JSON data
        Returns:
            dimensions (list): List of keys representing the parameters of the tests (nb_tasks, mesh_size, solvers, ...)
        """

        dimensions = data["testcases"][0]["check_params"].keys()

        for testcase in data["testcases"]:
            dims = testcase["check_params"]
            assert set(dimensions) == set(dims), f"A testcase has different dimensions {dimensions} and {dims}"

        self.dimensions = dimensions

    def buildMasterDf(self,data):
        """Build a dataframe where each row is indexed by a perfvar and its respective values
        Args:
            data (dict): The parsed JSON data
        """
        processed_data = []

        for i,testcase in enumerate(data["testcases"]):
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
                tmp_dct["is_partial"] = "is_partial" in testcase["tags"] and len(tmp_dct["performance_variable"].split("_"))>1
                tmp_dct["stage_name"] = tmp_dct["performance_variable"].split("_")[0]
                tmp_dct["partial_name"] = tmp_dct["performance_variable"].split("_")[1] if tmp_dct["is_partial"] else None
                tmp_dct["testcase_time_run"] = testcase["time_run"]

                for dim, v in testcase["check_params"].items():
                    tmp_dct[dim] = v

                processed_data.append(tmp_dct)

        self.master_df = pd.DataFrame(processed_data)

    def getDataForMetric(self, strategy):
        """ Apply a strategy to extract data for a specific metric
        Args:
            strategy (MetricStrategy): The strategy used to calculate or calculate the metric
        Returns:
            pd.DataFrame: Processed data for the specific metric.
        """
        return strategy.calculate(self.master_df)

class MetricStrategy:
    """ Abstract Strategy class for metrics"""
    def calculate(self,data):
        """ Calculates a metric from the data
        Args:
            data (pd.DataFrame): data to extract the metric from
        """
        raise NotImplementedError


class PerformanceByStageStrategy(MetricStrategy):
    """ Strategy to get the performance of a reframe test by the stage"""
    def __init__(self, unit, dimensions):
        """ Set the unit and dimensiosn
        Args:
            unit (str): Unit to filter by in order to not combine different values (e.g. Don't mix seconds with iterations)
            dimensions (list[str]): List of dimensions to index by (e.g. Mesh size, number of tasks, solvers, etc.)
        """
        self.unit = unit
        self.dimensions = dimensions

    def calculate(self, df):
        """ Groups the dataframe by stage name
        Args:
            df (pd.DataFrame) : the master dataframe
        Return:
            pd.DataFrame : Pivot dataframe having dimensions as index and stage names as columns
        """
        pivot = pd.pivot_table(df[df["unit"] == self.unit], values="value", index=self.dimensions,columns="stage_name",aggfunc="sum")
        if isinstance(pivot.index, pd.MultiIndex):
            raise NotImplementedError
        return pivot

class SpeedupByStageStrategy(MetricStrategy):
    def __init__(self,dimension):
        self.dimension = dimension

    def calculate(self,df):
        pivot = PerformanceByStageStrategy(unit="s",dimensions=[self.dimension]).calculate(df)
        pivot["Total"] = pivot.sum(axis=1)
        speedup = pd.DataFrame(pivot.loc[pivot.index.min(),:]/pivot)
        speedup["Optimal"] = speedup.index / speedup.index.min()
        speedup["HalfOptimal"] = speedup.index / (2*speedup.index.min())
        return speedup

class AtomicReportView:
    """ View component for the Atomic Report, it contains all figure generation related code """
    def plotScatters(self,df, title, yaxis_label):
        """ Create a plot with multiple lines
        Args:
            df (pd.DataFrame): Dataframe to create plot from, index goes to x axis and columns are line plots.
                                Values go on y-axis. The x-axis label is inferred from the dataframe's index name.
            title (str) : Title of the figure
            yaxis_label (str): Label of the y-axis
        Returns:
            go.Figure : Figure with multiple scatter plots
        """
        return go.Figure(
            data = [
                go.Scatter(
                    x = df.index,
                    y = df.loc[:,column],
                    name = column,
                )
                for column in df.columns
            ],
            layout=go.Layout(
                title=title,
                xaxis=dict( title = df.index.name ),
                yaxis=dict( title = yaxis_label )
            )
        )

    def plotTable(self,df, precision = 3):
        """ Create a plotly table with the same structure as the input dataframe
        Args:
            df (pd.DataFrame): Dataframe to create the table from.
        """
        return go.Figure(
            go.Table(
                header=dict(values= [df.index.name] + df.columns.tolist()),
                cells=dict(
                    values=[df.index.values.tolist()] + [df[col] for col in df.columns],
                    format=[f'.{precision}f' if t ==np.float64 else '' for t in [df.index.dtype] + df.dtypes.values.tolist()]
                )
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

    def generatePerformanceByStagePlot(self, strategy):
        """ Create multi-line scatter plot representing the performance of a test by stage.
        Args:
            strategy (MetricStrategy): The strategy used for metric extraction
        """
        data = self.model.getDataForMetric(strategy)
        return self.view.plotScatters(data,title="Performance By Stage",yaxis_label="s")

    def generatePerformanceByStageTable(self, strategy):
        data = self.model.getDataForMetric(strategy)
        return self.view.plotTable(data)
