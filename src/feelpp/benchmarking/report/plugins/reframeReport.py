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
                perfvar_df =  pd.DataFrame.from_dict(testcase["perfvalues"])
                perfvar_df = perfvar_df.iloc[:1,:]
                perfvar_df.rename(columns={c:c.split(":")[-1] for c in perfvar_df.columns},inplace=True)
                perfvar_df = perfvar_df.rename(columns={c:f"perfvalues.{c}" for c in perfvar_df})


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
        return pd.concat(runs_dfs,axis=0)
