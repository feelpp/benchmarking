from feelpp.benchmarking.report.strategies import PerformanceStrategy, RelativePerformanceStrategy, SpeedupStrategy, StrategyFactory
import pytest
import pandas as pd
import numpy as np
from itertools import product

class AxisMocker:
    def __init__(self, label="",parameter=""):
        self.label = label
        self.parameter = parameter

class PlotConfigMocker:
    def __init__(
        self, transformation="",aggregations = [],
        xaxis = AxisMocker(), secondary_axis= AxisMocker(), color_axis=AxisMocker(),
        variables = []
    ):
        self.transformation = transformation
        self.xaxis = xaxis
        self.secondary_axis = secondary_axis
        self.color_axis = color_axis
        self.aggregations = aggregations
        self.variables = variables

@pytest.mark.parametrize(("transformation","strategy"),[
    ("performance",PerformanceStrategy),
    ("relative_performance",RelativePerformanceStrategy),
    ("speedup",SpeedupStrategy),
    ("unkown",None)
])
def test_strategyFactory(transformation,strategy):
    if strategy:
        assert isinstance(StrategyFactory.create(PlotConfigMocker(transformation=transformation)),strategy)
    else:
        with pytest.raises(NotImplementedError):
            StrategyFactory.create(PlotConfigMocker(transformation=transformation))


class TestSimpleStrategies:
    """Tests for strategies with simple confiugurations (just xaxis)"""
    plot_config = PlotConfigMocker( xaxis=AxisMocker(parameter="xaxis",label="x") )

    parameter_product = list(product([2,4,8,16,32,64,128],["a","b","c","d"]))

    mock_data = pd.DataFrame(
        {
            "some_col":["sample_data"]*len(parameter_product),
            "xaxis" : [p[0] for p in parameter_product],
            "performance_variable": [p[1] for p in parameter_product],
            "value": np.random.uniform(-100,100,len(parameter_product))
        }
    )

    def getCalculatedDf(self,transformation):
        self.plot_config.transformation = transformation
        calculated_df = StrategyFactory.create(self.plot_config).calculate(self.mock_data)
        assert calculated_df.index.name == "xaxis"
        assert calculated_df.columns.name == "performance_variable"
        assert calculated_df.isna().sum().sum() == 0

        return calculated_df

    def test_performanceStrategy(self):
        """Tests for the performance strategy"""
        calculated_df = self.getCalculatedDf("performance")
        for x,c,v in zip(self.mock_data["xaxis"],self.mock_data["performance_variable"],self.mock_data["value"]):
            assert calculated_df.loc[x,c] == v

    def test_relativePerformanceStrategy(self):
        """Tests for the relative performance strategy"""
        calculated_df = self.getCalculatedDf("relative_performance")
        assert np.isclose(calculated_df.sum(axis=1),100).all(), "sum is not 100"

        pivot = self.getCalculatedDf("performance")
        totals = pivot.sum(axis=1)
        assert np.isclose(calculated_df,100*(pivot.T /totals).T).all()

    def test_speedupStrategy(self):
        """Tests for the speedup strategy"""
        calculated_df = self.getCalculatedDf("speedup")
        assert np.isclose(calculated_df.loc[calculated_df.index.min(),:],1).all()
        pivot = self.getCalculatedDf("performance")
        assert np.isclose(calculated_df,pivot.loc[pivot.index.min(),:] / pivot).all()

class TestComplexStrategies:
    plot_config = PlotConfigMocker(
        xaxis=AxisMocker(parameter="xaxis",label="x"),
        secondary_axis=AxisMocker(parameter="secondary_axis",label="secondary"),
        color_axis=AxisMocker(parameter="color_axis",label="color")
    )

    parameter_product = list(product([32,64,128],["M1","M2"],["A","B","C"]))

    mock_data = pd.DataFrame(
        {
            "some_col":["sample_data"]*len(parameter_product),
            "xaxis" : [p[0] for p in parameter_product],
            "color_axis" : [p[1] for p in parameter_product],
            "secondary_axis": [p[2] for p in parameter_product],
            "value": np.random.uniform(-100,100,len(parameter_product)),
            "performance_variable":["a"]*len(parameter_product)
        }
    )

    def getCalculatedDf(self,transformation):
        self.plot_config.transformation = transformation
        calculated_df = StrategyFactory.create(self.plot_config).calculate(self.mock_data)
        assert calculated_df.index.names[0] == "secondary_axis"
        assert calculated_df.index.names[1] == "xaxis"
        assert calculated_df.columns.name == "color_axis"
        assert calculated_df.isna().sum().sum() == 0

        return calculated_df

    def test_performanceStrategy(self):
        """Tests for the performance strategy"""
        calculated_df = self.getCalculatedDf("performance")
        for s,x,c,v in zip(self.mock_data["secondary_axis"],self.mock_data["xaxis"],self.mock_data["color_axis"],self.mock_data["value"]):
            assert calculated_df.loc[(s,x),c] == v

    def test_relativePerformanceStrategy(self):
        """Tests for the relative performance strategy"""
        calculated_df = self.getCalculatedDf("relative_performance")
        assert np.isclose(calculated_df.sum(axis=1),100).all(), "sum is not 100"

        pivot = self.getCalculatedDf("performance")
        assert np.isclose(calculated_df,100*(pivot.T / pivot.sum(axis=1)).T).all()


    def test_speedupStrategy(self):
        """Tests for the relative performance strategy"""
        calculated_df = self.getCalculatedDf("speedup")
        assert np.isclose(calculated_df.loc[calculated_df.index.min(),:],1).all()
        pivot = self.getCalculatedDf("performance")
        assert np.isclose(calculated_df,pivot.xs(pivot.index.get_level_values("xaxis").min(),level="xaxis",axis=0) / pivot).all()

