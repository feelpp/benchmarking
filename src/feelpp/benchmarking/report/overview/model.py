import pandas as pd
from feelpp.benchmarking.report.base.model import Model



class OverviewModel(Model):
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

