""" Tests related to plots configuration """
import pytest
from feelpp.benchmarking.dashboardRenderer.schemas.ConfigPlots import Plot, Aggregation, PlotAxis
from pydantic import ValidationError

class TestAggregation:
    """ Tests for the Aggregation pydantic schema """
    def test_validAgg(self):
        """ Tests that aggregation functions are correctly validated """
        agg = Aggregation(column="test",agg="sum")
        assert agg.agg == "sum"

        with pytest.raises(NotImplementedError):
            agg = Aggregation(column="test",agg="not implemented agg")


class TestPlot:
    """ Tests for the Plot pydantic schema"""
    def test_checkValidAxis(self):
        """ Tests that the axis is correctly validated"""

        plot = Plot(title="t",plot_types=["scatter"],transformation="performance",xaxis=PlotAxis(parameter="param",label="x"),yaxis=PlotAxis(label="y"))
        assert plot.xaxis.parameter

        with pytest.raises(ValidationError):
            plot = Plot(title="t",plot_types=["scatter"],transformation="performance",xaxis=PlotAxis(label="x"),yaxis=PlotAxis(label="y"))
        with pytest.raises(ValidationError):
            plot = Plot(title="t",plot_types=["scatter"],transformation="performance",xaxis=PlotAxis(label="x"),yaxis=PlotAxis(label="y"),secondary_axis=PlotAxis(label="secondary",parameter="secondary_param"))

