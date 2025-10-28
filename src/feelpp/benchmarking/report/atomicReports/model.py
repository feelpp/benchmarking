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
            if "perfvalues" not in testcase or not testcase["perfvalues"] or testcase["perfvalues"] == {}:
                tmp_dct = {
                    "performance_variable": "",
                    "value": None,
                    "unit": "",
                    "reference": None,
                    "thres_lower": None,
                    "thres_upper": None,
                    "status": None,
                    "absolute_error": None,
                    "testcase_time_run": testcase["time_run"],
                    "environment":testcase["environ"] if "environ" in testcase else "",
                    "platform":testcase["platform"] if "platform" in testcase else ""
                }
                for dim, v in testcase["check_params"].items():
                    if isinstance(v,dict):
                        for subdim, v2 in v.items():
                            tmp_dct[f"{dim}.{subdim}"] = v2
                    else:
                        tmp_dct[dim] = v
                processed_data.append(tmp_dct)
                continue

            for name,perfvars in testcase["perfvalues"].items():
                tmp_dct = {}
                tmp_dct["performance_variable"] = name.split(":")[-1]
                tmp_dct["value"] = float(perfvars[0])
                tmp_dct["unit"] = perfvars[4]
                tmp_dct["reference"] = float(perfvars[1]) if perfvars[1] else np.nan
                tmp_dct["thres_lower"] = float(perfvars[2]) if perfvars[2] else np.nan
                tmp_dct["thres_upper"] = float(perfvars[3]) if perfvars[3] else np.nan
                tmp_dct["status"] = tmp_dct["thres_lower"] <= tmp_dct["value"] <= tmp_dct["thres_upper"] if not np.isnan(tmp_dct["thres_lower"]) and not np.isnan(tmp_dct["thres_upper"]) else np.nan
                tmp_dct["absolute_error"] = np.abs(tmp_dct["value"] - tmp_dct["reference"])
                tmp_dct["testcase_time_run"] = testcase["time_run"]
                tmp_dct["environment"] = testcase["environ"] if "environ" in testcase else ""
                tmp_dct["platform"] = testcase["platform"] if "platform" in testcase else ""

                for dim, v in testcase["check_params"].items():
                    if isinstance(v,dict):
                        for subdim, v2 in v.items():
                            tmp_dct[f"{dim}.{subdim}"] = v2
                    else:
                        tmp_dct[dim] = v

                processed_data.append(tmp_dct)

        return pd.DataFrame(processed_data)