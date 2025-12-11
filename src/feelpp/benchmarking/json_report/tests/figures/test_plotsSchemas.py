""" Tests related to plots configuration """
import pytest
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot, Aggregation, PlotAxis
from pydantic import ValidationError

class TestPlotSchemas:

    # ------------------------------------------------------------------
    # PlotAxis: filter parsing
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("inputValue,expected",
        [
            ("val", [{"val":"val"}]),
            (["val1","val2"], [{"val1":"val1"},{"val2":"val2"}]),
            ({"key":"custom"}, [{"key":"custom"}]),
            ([{"a":"b"},{"c":"d"}], [{"a":"b"},{"c":"d"}])
        ]
    )
    def test_parseFilterAxisParsesCorrectly(self, inputValue, expected):
        axis = PlotAxis(parameter="x", filter=inputValue)
        assert axis.filter == expected

    def test_parseFilterAxisInvalidRaises(self):
        with pytest.raises(ValueError):
            PlotAxis(parameter="x", filter=123)

    # ------------------------------------------------------------------
    # PlotAxis: default label
    # ------------------------------------------------------------------
    def test_defaultLabelIsParameterTitle(self):
        axis = PlotAxis(parameter="runtime")
        assert axis.label == "Runtime"

    def test_labelPreservedIfProvided(self):
        axis = PlotAxis(parameter="runtime", label="Execution Time")
        assert axis.label == "Execution Time"

    # ------------------------------------------------------------------
    # Aggregation: valid agg methods
    # ------------------------------------------------------------------
    @pytest.mark.parametrize( "aggMethod",
        ["sum","mean","min","max","first","count","nunique","filter:custom"]
    )
    def test_checkAggAcceptsValidMethods(self, aggMethod):
        agg = Aggregation(column="score", agg=aggMethod)
        assert agg.agg == aggMethod

    def test_checkAggInvalidRaises(self):
        with pytest.raises(NotImplementedError):
            Aggregation(column="score", agg="median")

    # ------------------------------------------------------------------
    # Plot: xaxis and secondary_axis must have parameter
    # ------------------------------------------------------------------
    def test_checkAxisValid(self):
        xaxis = PlotAxis(parameter="x")
        yaxis = PlotAxis(parameter="y")
        plot = Plot( title="Test Plot", plot_types=["scatter"], xaxis=xaxis, yaxis=yaxis )
        assert plot.xaxis.parameter == "x"
        assert plot.yaxis.parameter == "y"

    def test_checkAxisMissingParameterRaises(self):
        with pytest.raises(ValidationError):
            Plot(title="Test Plot",plot_types=["scatter"],xaxis=PlotAxis(parameter=None),yaxis=PlotAxis(parameter="y"))

    # ------------------------------------------------------------------
    # Plot: full creation with optional fields
    # ------------------------------------------------------------------
    def test_plotCreationWithAllOptionalFields(self):
        xaxis = PlotAxis(parameter="x")
        yaxis = PlotAxis(parameter="y")
        secondary = PlotAxis(parameter="sec")
        color = PlotAxis(parameter="col")
        extra = [PlotAxis(parameter="extra1"), PlotAxis(parameter="extra2")]
        aggs = [Aggregation(column="score", agg="sum")]

        plot = Plot(
            title="Full Plot", plot_types=["scatter","table"], transformation="performance", aggregations=aggs, xaxis=xaxis,
            secondary_axis=secondary, yaxis=yaxis, color_axis=color, extra_axes=extra, layout_modifiers={"width":800}
        )

        assert plot.title == "Full Plot"
        assert plot.transformation == "performance"
        assert plot.aggregations[0].agg == "sum"
        assert len(plot.extra_axes) == 2
        assert plot.layout_modifiers["width"] == 800