import os
from pandas import MultiIndex

class Figure:
    def __init__(self,plot_config):
        self.config = plot_config

    def getIdealRange(self,df):
        """ Computes the [(min - eps), (max+eps)] interval for optimal y-axis display
        Args:
            - df (pd.DataFrame): The dataframe for which the interval should be computed
        Returns list[float, float]: The  [(min - eps), (max+eps)] interval
        """
        range_epsilon= 0.01
        return [ df.min().min() - df.min().min()*range_epsilon, df.max().max() + df.min().min()*range_epsilon ]

    def createMultiindexFigure(self,df,data_dirpath):
        raise NotImplementedError("Pure virtual function. Not to be called from the base class")

    def createSimpleFigure(self,df,data_dirpath):
        raise NotImplementedError("Pure virtual function. Not to be called from the base class")

    def sanitizeFilename(self,title:str):
        """Creates a FS friendly filename. Mostly used to be latex compatible"""
        t = str(title).replace(" ","-").replace("_","-")
        return "".join(x for x in t if x.isalnum() or x in ["-","."])

    def createCsvs(self,df):
        """Creates the corresponding csv strings for the figure
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            list[dict[str,str]]: A list of dictionaries containing the csv strings and their corresponding titles.
            Schema: [{"filename":str, "data":str}]
        """
        if isinstance(df.index,MultiIndex):
            return [{"filename":f"{self.sanitizeFilename(key)}.csv", "data":df.xs(key, level=0).to_csv()} for key in df.index.levels[0]]
        else:
            return [{"filename":f"{self.sanitizeFilename(self.config.title)}.csv", "data":df.to_csv()}]

    def createFigure(self,df,data_dirpath, **args):
        """ Creates a figure from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the grouped Bar type
        """
        if isinstance(df.index,MultiIndex):
            figure = self.createMultiindexFigure(df,data_dirpath, **args)
        else:
            figure = self.createSimpleFigure(df, data_dirpath, **args)

        return figure

    def createJson(self,df):
        raise NotImplementedError
