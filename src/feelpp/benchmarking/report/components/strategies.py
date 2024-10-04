import pandas as pd
from sklearn.linear_model import LinearRegression

class MetricStrategy:
    """ Abstract Strategy class for metrics"""
    def calculate(self,data):
        """ Calculates a metric from the data
        Args:
            data (pd.DataFrame): data to extract the metric from
        """
        raise NotImplementedError


class PerformanceStrategy(MetricStrategy):
    """ Strategy to get the performance of a reframe test by the stage"""
    def __init__(self, unit, dimensions,stage=None):
        """ Set the unit and dimensiosn
        Args:
            unit (str): Unit to filter by in order to not combine different values (e.g. Don't mix seconds with iterations)
            dimensions (list[str]): List of dimensions to index by (e.g. Mesh size, number of tasks, solvers, etc.)
            stage (str): Name of the stage to filter. If None, the performance by stage is computed. Defaults to None.
        """
        self.unit = unit
        self.dimensions = dimensions
        self.stage = stage

    def calculate(self, df):
        """ Groups the dataframe by stage name
        Args:
            df (pd.DataFrame) : the master dataframe
        Return:
            pd.DataFrame : Pivot dataframe having dimensions as index and stage names as columns
        """
        if not self.stage:
            pivot = pd.pivot_table(df[(df["unit"] == self.unit)], values="value", index=self.dimensions,columns="stage_name",aggfunc="sum")
            pivot.name = None
        else:
            pivot = pd.pivot_table(df[(df["unit"] == self.unit)&(df["stage_name"] == self.stage)], values="value", index=self.dimensions,columns="partial_name",aggfunc="sum")
            pivot.name = self.stage

        if isinstance(pivot.index, pd.MultiIndex):
            raise NotImplementedError
        return pivot

class SpeedupStrategy(MetricStrategy):
    """ Strategy to get the speedup of a reframe test by the stage, depending on the dimension"""
    def __init__(self,dimension,stage = None):
        self.dimension = dimension
        self.stage = stage

    def calculate(self,df):
        """ Compute the speedup for a given dimension, including optimal and half optimal speedups
        Args
            df (pd.DataFrame) : The master dataframe
        Returns:
            pd.DataFrame, Dataframe having the dimension (nb_cores, mesh size) in index and stage as columns ( including total, optimal and half-optimal speedup)
        """
        pivot = PerformanceStrategy(unit="s",dimensions=[self.dimension],stage=self.stage).calculate(df)

        speedup = pd.DataFrame(pivot.loc[pivot.index.min(),:]/pivot)

        for col in pivot.columns:
            model = LinearRegression()
            tmp = speedup.loc[:,col].dropna(axis=0)
            x = tmp.index.values.reshape(-1,1)
            y = tmp.values
            model.fit(x,y)
            speedup.loc[tmp.index,col+"_linearReg"] = model.predict(x)

        speedup["Optimal"] = speedup.index / speedup.index.min()
        speedup["HalfOptimal"] = speedup.index / (2*speedup.index.min())

        speedup.name = self.stage

        return speedup


