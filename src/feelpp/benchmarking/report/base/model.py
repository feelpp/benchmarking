import pandas as pd
class Model:
    """ Abstract model component """
    def __init__(self):
        pass

    def buildMasterDf(self):
        pass


class AggregationModel(Model):
    """ Model used for aggregating data other models """
    def __init__(self, dfs_dict,index_label):
        self.master_df = self.buildMasterDf(dfs_dict,index_label)

    def buildMasterDf(self,dfs_dict,index_label):
        """ Concatenates the given dataframes on the row axis, adding the dfs_dict keys as a new column
        Args:
            dfs_dict (dict): Dictionary in the form of {index : dataframe} containing all dataframes to aggregate. It also acepts serialized dataframes.
            index_label (str) label of the new column
        """
        parsed_dfs = []
        for ind, df in dfs_dict.items():
            parsed_df = pd.DataFrame(df)
            parsed_df[index_label] = ind
            parsed_dfs.append(parsed_df)

        return pd.concat(parsed_dfs,axis=0,ignore_index=True)


    @classmethod
    def fromDataframe(cls, df):
        """ Initialize the class from an already merged dataframe"""
        cls.master_df = pd.DataFrame(df)
        return cls