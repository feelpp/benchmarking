import pandas as pd


class TransformationStrategy:
    """ Abstract class for transformation strategies"""
    def __init__(self):
        pass

    def calculate(self,df):
        """ abstract method for transforming a dataframe depending on the strategy"""
        raise NotImplementedError("Not to be called directly.")


class PerformanceStrategy(TransformationStrategy):
    """ Strategy that pivots a dataframe on given dimensions"""
    def __init__(self,dimensions,variables):
        super().__init__()
        self.dimensions = dimensions
        self.variables = variables

    def calculate(self,df):
        """ Pivots dataframe, setting "performance_variable" values as columns, "value" as cell values, and dimensions as indexes.
            Then filters depending on the specified variables
            If the dataframe contains duplicated values for a given dimension, the values are aggregated (mean).
        Args:
            df (pd.DataFrame): The master dataframe containing all the data from the reframe test
        Returns:
            pd.DataFrame: The pivoted and filtered dataframe (can be multiindex)
        """
        return pd.pivot_table(df,values="value",columns="performance_variable",index=self.dimensions,aggfunc="mean").loc[:,self.variables]

class SpeedupStrategy(TransformationStrategy):
    """ Strategy that computes the speedup of a dataset on given dimensions """
    def __init__(self,dimensions,variables):
        super().__init__()
        self.dimensions = dimensions
        self.variables = variables

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
        pivot = PerformanceStrategy(
            dimensions=self.dimensions,
            variables=self.variables
        ).calculate(df)

        if isinstance(pivot.index, pd.MultiIndex):
            return pivot.xs(pivot.index.get_level_values(self.dimensions[0]).min(),level=self.dimensions[0],axis=0) / pivot
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
        dimensions = [plot_config.xaxis.parameter]
        if plot_config.animation_axis and plot_config.animation_axis.parameter:
            dimensions.append(plot_config.animation_axis.parameter)
        if plot_config.yaxis and plot_config.yaxis.parameter:
            dimensions.append(plot_config.yaxis.parameter)

        match plot_config.transformation:
            case "performance":
                return PerformanceStrategy(
                    dimensions=dimensions,
                    variables=plot_config.variables
                )
            case "speedup":
                return SpeedupStrategy(
                    dimensions=dimensions,
                    variables=plot_config.variables
                )
            case _:
                raise NotImplementedError

