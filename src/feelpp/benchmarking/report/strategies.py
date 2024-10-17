import pandas as pd


class TransformationStrategy:
    """ Abstract class for transformation strategies"""
    def __init__(self,dimensions,variables):
        self.dimensions = dimensions
        self.variables = variables
        pass

    def calculate(self,df):
        """ abstract method for transforming a dataframe depending on the strategy"""
        raise NotImplementedError("Not to be called directly.")


class PerformanceStrategy(TransformationStrategy):
    """ Strategy that pivots a dataframe on given dimensions"""
    def __init__(self,dimensions,variables):
        super().__init__(dimensions,variables)

    def calculate(self,df):
        """ Pivots dataframe, setting "performance_variable" values as columns, "value" as cell values, and dimensions as indexes.
            Then filters depending on the specified variables
            If the dataframe contains duplicated values for a given dimension, the values are aggregated (mean).
        Args:
            df (pd.DataFrame): The master dataframe containing all the data from the reframe test
        Returns:
            pd.DataFrame: The pivoted and filtered dataframe (can be multiindex)
        """
        index = []
        if self.dimensions["secondary_axis"]:
            index.append(self.dimensions["secondary_axis"])
        if self.dimensions["xaxis"]:
            index.append(self.dimensions["xaxis"])
        return df[df["performance_variable"].isin(self.variables)].pivot(index=index,values="value",columns=self.dimensions["color_axis"])

class RelativePerformanceStrategy(PerformanceStrategy):
    """ Strategy that pivots a dataframe on given dimensions and computes the relative (%) values to the sum of the columns"""
    def __init__(self,dimensions,variables):
        super().__init__(dimensions,variables)

    def calculate(self,df):
        """ Pivots dataframe, setting "performance_variable" values as columns, "value" as cell values, and dimensions as indexes.
            Then filters depending on the specified variables
            If the dataframe contains duplicated values for a given dimension, the values are aggregated (mean).
            Finally, the relative values to the total (percentage) are computed, for each one of the columns.
        Args:
            df (pd.DataFrame): The master dataframe containing all the data from the reframe test
        Returns:
            pd.DataFrame: The pivoted and filtered relative (%) values dataframe (can be multiindex)
        """
        pivot = super().calculate(df)
        return 100*((pivot.T / pivot.sum(axis=1)).T)

class PerformanceSumStrategy(TransformationStrategy):
    """ Strategy that pivots a dataframe on given dimensions and sums values"""
    def __init__(self,dimensions,variables):
        super().__init__(dimensions,variables)

    def calculate(self,df):
        index = []
        if self.dimensions["secondary_axis"]:
            index.append(self.dimensions["secondary_axis"])
        if self.dimensions["xaxis"]:
            index.append(self.dimensions["xaxis"])
        return df[df["performance_variable"].isin(self.variables)].pivot_table(index=index,values="value",columns=self.dimensions["color_axis"],aggfunc="sum")



class SpeedupStrategy(PerformanceStrategy):
    """ Strategy that computes the speedup of a dataset on given dimensions """
    def __init__(self,dimensions,variables):
        super().__init__(dimensions,variables)

    def calculate(self,df):
        """ Computes the "speedup" of the data for the FIRST dimension specified.
            Pivots dataframe, setting "performance_variable" values as columns, "value" as cell values, and dimensions as indexes.
            Then filters depending on the specified variables
            If the dataframe contains duplicated values for a given dimension, the values are aggregated (mean).
            Finally, the speedup is computed on the pivot
        Args:
            df (pd.DataFrame): The master dataframe containing all the data from the reframe test
        Returns:
            pd.DataFrame: The pivoted dataframe representing the speedup (can be multiindex)
        """
        pivot = super().calculate(df)

        if isinstance(pivot.index, pd.MultiIndex):
            return pivot.xs(pivot.index.get_level_values(self.dimensions["xaxis"]).min(),level=self.dimensions["xaxis"],axis=0) / pivot
        else:
            return pivot.loc[pivot.index.min(),:] / pivot


class StrategyFactory:
    """ Factory class to dispatch concrete transformation strategies"""
    @staticmethod
    def create(plot_config):
        """ Creates a concrete strategy
        Args:
            plot_config (Plot). Pydantic object with the plot configuration information
        """
        dimensions = {
            "xaxis" : plot_config.xaxis.parameter,
            "secondary_axis" : plot_config.secondary_axis.parameter if plot_config.secondary_axis and plot_config.secondary_axis.parameter else None,
            "color_axis" : plot_config.color_axis.parameter if plot_config.color_axis and plot_config.color_axis.parameter else "performance_variable",
        }

        if plot_config.transformation == "performance":
            return PerformanceStrategy(dimensions=dimensions,variables=plot_config.variables)
        elif plot_config.transformation == "speedup":
            return SpeedupStrategy(dimensions=dimensions,variables=plot_config.variables)
        elif plot_config.transformation == "relative_performance":
            return RelativePerformanceStrategy(dimensions=dimensions,variables=plot_config.variables)
        elif plot_config.transformation =="performance_sum":
            return PerformanceSumStrategy(dimensions=dimensions,variables=plot_config.variables)
        else:
            raise NotImplementedError

