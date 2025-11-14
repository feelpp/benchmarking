import pandas as pd


class ReframeReportPlugin:
    @staticmethod
    def process(template_data):
        if "rfm" in template_data:
            return {"reframe_runs_df" : ReframeReportPlugin.runsToDf(template_data["rfm"]["runs"])}
        return {"reframe_runs_df" : pd.DataFrame() }

    @staticmethod
    def aggregator(node_id, repository_type, template_data, child_results):
        child_dfs = [c.get("data") for c in child_results if c and "data" in c]
        own_df = template_data.get("reframe_runs_df")
        if own_df is not None:
            if repository_type == "leaves":
                own_df["date"] = pd.to_datetime(template_data["title"],format="%Y_%m_%dT%H_%M_%S")
            child_dfs.append(own_df)

        if not child_dfs:
            merged = None
        else:
            merged = pd.concat(child_dfs, ignore_index=True)
            if repository_type:
                merged[repository_type] = node_id

        children_repositories = {c.get("repository_type") for c in child_results}

        return {
            "data": merged,
            "repository_type":repository_type,
            "children_repositories": children_repositories,
            "summary":{child_repo_type : ReframeReportPlugin.summarizeReports(merged,child_repo_type) for child_repo_type in children_repositories}
        }

    @staticmethod
    def summarizeReports(df: pd.DataFrame, repository_type):
        if df is None or df.empty or not repository_type:
            return pd.DataFrame()

        leaf_summary = df.groupby("leaves").agg(
            num_runs=("runs.run_index", lambda x: x.max() + 1),
            date=("date", "first"),
            num_cases=("runs.num_cases", "first"),
            num_failures=("runs.num_failures", "first"),
            result=("result", lambda x: "pass" if (x == "pass").all() else "fail"),
            repo_value=(repository_type, "first"),
        )

        if repository_type == "leaves":
            return leaf_summary.sort_values("date", ascending=False).reset_index().set_index("date")

        repo_summary = leaf_summary.groupby("repo_value").agg(
            num_runs=("num_runs", "sum"),
            num_cases=("num_cases", "sum"),
            num_failures=("num_failures", "sum"),
            result=("result", lambda x: "pass" if (x == "pass").all() else "fail"),
        )

        return repo_summary.reset_index().rename(columns={"repo_value": repository_type}).set_index(repository_type)


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
                else:
                    perfvar_df = pd.DataFrame([{
                        "system": testcase.get("system", None), "partition": testcase.get("partition", None),
                        "perfvalue": None,
                        "value": None, "reference": None, "low_threshold": None, "up_threshold": None, "unit": None,
                        "result": testcase.get("result", None)
                    }])


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

    @staticmethod
    def mergetLeafData( parent_id, leaves_info ):
        dfs = []
        for leaf_id, leaf_data in leaves_info:
            leaf_df = leaf_data["reframe_runs_df"].copy()
            leaf_df["report"] = leaf_id
            dfs.append(leaf_df)
        return pd.concat(dfs, axis=0, ignore_index=True)

    @staticmethod
    def mergeComponentData(parent_id, component_id, children_data, repo_name=None):
        combined_df = pd.concat(children_data, axis=0, ignore_index=True)
        combined_df["parent"] = parent_id
        combined_df["component"] = component_id
        return combined_df