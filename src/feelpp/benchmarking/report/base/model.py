import pandas as pd
class Model:
    """ Abstract model component """
    def __init__(self):
        pass

    def buildMasterDf(self):
        pass


class AggregationModel(Model):
    def __init__(self, dfs_dict,index_label):
        self.master_df = self.buildMasterDf(dfs_dict,index_label)

    def buildMasterDf(self,dfs_dict,index_label):
        parsed_dfs = []
        for ind, df in dfs_dict.items():
            parsed_df = pd.DataFrame(df)
            parsed_df = parsed_df.T.set_index([[ind]*df.shape[1],parsed_df.columns]).T
            parsed_df.columns = parsed_df.columns.rename([index_label]+parsed_df.columns.names[1:])
            parsed_dfs.append(parsed_df)

        return pd.concat(parsed_dfs,axis=0,ignore_index=False).sort_index()

    @classmethod
    def fromDataframe(cls, df):
        cls.master_df = pd.DataFrame(df)
        return cls