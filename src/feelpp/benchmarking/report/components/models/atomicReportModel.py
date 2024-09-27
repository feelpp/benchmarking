import json
import numpy as np
import pandas as pd

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
