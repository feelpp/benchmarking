from feelpp.benchmarking.report.base.model import Model
import numpy as np
import pandas as pd

class AtomicReportModel(Model):
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

class AtomicOverviewModel(Model):
    """ Model component of the useCase.
        This class holds the aggregated data for all atomic reports in a use case.
    """
    def __init__(self, atomic_models_dfs):
        self.master_df = self.buildMasterDf( atomic_models_dfs )

    def buildMasterDf(self,atomic_models_dfs):
        """ creates a dataframe holding all master dataframes from atomic reports.
            Facilitates pivoting and aggregation
        Args:
            atomic_models_dfs (dict[pd.DataFrame]). Dict with atomic report master dataframes (serialized with to_dict(orient='dict')), keys are report's start and end times as tuple
        """
        parsed_dfs = []
        for date, df in atomic_models_dfs.items():
            parsed_df = pd.DataFrame.from_records(df)
            parsed_df["time_start"] = date
            parsed_dfs.append(parsed_df)

        return pd.concat(parsed_dfs ,axis=0)

