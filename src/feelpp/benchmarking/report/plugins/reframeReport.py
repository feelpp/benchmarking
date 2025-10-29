import pandas as pd


class ReframeReport:


    @staticmethod
    def runsToDf(runs):
        runs_dfs = []
        for run in runs:
            run_df = pd.DataFrame.from_dict(run,orient="index").T.drop(columns="testcases")
            run_df = run_df.rename(columns={c:f"runs.{c}" for c in run_df.columns})
            testcases = []
            for testcase in run["testcases"]:
                perfvar_df = pd.DataFrame()
                if "perfvalues" in testcase and testcase["perfvalues"] and testcase["perfvalues"] != {}:
                    perfvar_df =  pd.DataFrame.from_dict(testcase["perfvalues"])
                    perfvar_df = perfvar_df.rename(index={0:"value",1:"reference",2:"low_threshold",3:"up_threshold",4:"unit",5:"result"})
                    perfvar_df = perfvar_df.T.reset_index().rename(columns={"index":"perfvalue"})
                    perfvar_df[["system","partition","perfvalue"]] = perfvar_df["perfvalue"].str.split(":",expand=True)
                testcase_df = pd.DataFrame.from_dict(testcase,orient="index").T.drop(columns=["perfvalues","check_params"]+list(testcase["check_params"].keys()))
                testcase_df = testcase_df.rename(columns={c:f"testcases.{c}" for c in testcase_df})
                param_dict = {}
                for dim, v in testcase["check_params"].items():
                    if isinstance(v,dict):
                        for subdim, v2 in v.items():
                            param_dict[f"{dim}.{subdim}"] = v2
                    else:
                        param_dict[dim] = v
                param_df = pd.DataFrame.from_dict(param_dict,orient="index").T

                testcase_df = pd.concat([testcase_df,param_df],axis=1)
                testcases.append(pd.concat([perfvar_df,testcase_df.loc[testcase_df.index.repeat(perfvar_df.shape[0])].reset_index(drop=True)],axis=1))

            testcases_df = pd.concat(testcases,axis=0)
            runs_dfs.append(pd.concat([testcases_df,run_df.loc[run_df.index.repeat(perfvar_df.shape[0])].reset_index(drop=True)],axis=1))
        pd.concat(runs_dfs,axis=0).to_csv("ex.csv")
        return pd.concat(runs_dfs,axis=0)
