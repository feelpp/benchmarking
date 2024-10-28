import pandas as pd


class TransformationStrategy:
    """ Abstract class for transformation strategies"""
    def __init__(self,dimensions,aggregations,variables):
        self.dimensions = dimensions
        self.variables = variables
        self.aggregations = aggregations
        pass

    def calculate(self,df):
        """ abstract method for transforming a dataframe depending on the strategy"""
        raise NotImplementedError("Not to be called directly.")


class PerformanceStrategy(TransformationStrategy):
    """ Strategy that pivots a dataframe on given dimensions"""
    def __init__(self,dimensions,aggregations,variables):
        super().__init__(dimensions,aggregations,variables)

    def calculate(self,df):
        """ Pivots dataframe, setting the color axis parameter values as columns, "value" as cell values, and the xaxis and secondary axis parameters as indexes.
            Then filters depending on the specified variables
            If the configuration contains aggregations, they will be performed IN ORDER.
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

        pivot = df[df["performance_variable"].isin(self.variables or df["performance_variable"].unique())]

        if self.aggregations:
            agg_columns = index + [self.dimensions["color_axis"]] + [a.column for a in self.aggregations ]

            for aggregation in self.aggregations:
                agg_columns.remove(aggregation.column)
                pivot = pivot.groupby(agg_columns)["value"].agg(aggregation.agg).reset_index()

        return pivot.pivot(index=index,values="value",columns=self.dimensions["color_axis"])

class RelativePerformanceStrategy(PerformanceStrategy):
    """ Strategy that pivots a dataframe on given dimensions and computes the relative (%) values to the sum of the columns"""
    def __init__(self,dimensions,aggregations,variables):
        super().__init__(dimensions,aggregations,variables)

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


class SpeedupStrategy(PerformanceStrategy):
    """ Strategy that computes the speedup of a dataset on given dimensions """
    def __init__(self,dimensions,aggregations,variables):
        super().__init__(dimensions,aggregations,variables)

    def calculate(self,df):
        """ Computes the "speedup" of the data for the xaxis parameter.
            Pivots dataframe, setting coloraxis values as columns, "value" as cell values, and dimensions as indexes.
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
        aggregations = plot_config.aggregations

        if plot_config.transformation == "performance":
            return PerformanceStrategy(dimensions,aggregations,plot_config.variables)
        elif plot_config.transformation == "speedup":
            return SpeedupStrategy(dimensions,aggregations,plot_config.variables)
        elif plot_config.transformation == "relative_performance":
            return RelativePerformanceStrategy(dimensions,aggregations,plot_config.variables)
        else:
            raise NotImplementedError

