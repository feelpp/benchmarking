import pytest
from feelpp.benchmarking.report.figureFactory import FigureFactory
from feelpp.benchmarking.report.transformationFactory import TransformationStrategyFactory
from feelpp.benchmarking.report.dataGenerationStrategies import DataGeneratorFactory, PlotlyGenerator, PlotlyHtmlGenerator, CsvGenerator, PgfGenerator
from test_transformationStrategies import PlotConfigMocker, AxisMocker, MockDataframe
import pandas as pd
import numpy as np

class TestDataGeneratorStrategies:
    """ Tests all DataGenerator strategies. Compares the computed result of the strategy methods against the expected result"""

    plot_config = PlotConfigMocker(
        xaxis=AxisMocker(parameter="xaxis",label="x"),
        secondary_axis=AxisMocker(parameter="secondary_axis",label="secondary"),
        color_axis=AxisMocker(parameter="color_axis",label="color"),
        transformation="performance",
        plot_types=["scatter","stacked_bar"]
    )
    mock_data = MockDataframe("multi").df

    def getData(self,generator):
        """ Calls the generate method of a given strategy (generator), performs basic common tests and returns the data"""
        data = generator.generate([self.plot_config], self.mock_data)
        assert isinstance(data,list)
        assert len(data) == len(self.plot_config.plot_types), "Different number of generated data and plot_types "
        return data

    def test_plotlyGenerator(self):
        """ Tests for the PlotlyGenerator strategy.
        Checks that figures are identical as expected ones
        """
        generator = PlotlyGenerator()
        figures = self.getData(generator)

        expected_figures = [plot.createFigure(self.mock_data) for plot in FigureFactory.create(self.plot_config)]

        assert figures == expected_figures, "Figures are not the same as returned by the FigureFactory"

    def test_plotlyHtmlGenerator(self):
        """ Tests for the plotlyHtmlGenerator strategy.
        - Checks that figures start and end with an html tag
        - Checks that html strings have expected lenghts
        """
        generator = PlotlyHtmlGenerator()
        figures = self.getData(generator)
        expected_figures = [plot.createFigure(self.mock_data).to_html() for plot in FigureFactory.create(self.plot_config)]

        assert all([fig.startswith("<html>") and fig.endswith("</html>") for fig in figures]), "Figures do not start or end with html tags"
        assert all([len(fig) == len(expected_fig) for fig,expected_fig in zip(figures,expected_figures)]), "Figures html does not have the expected length"

    def test_csvGenerator(self):
        """Tests for the csvGenerator strategy"""
        generator = CsvGenerator()
        data = self.getData(generator)
        expected_data = [TransformationStrategyFactory.create(self.plot_config).calculate(self.mock_data).to_csv() for _ in self.plot_config.plot_types]

        assert all([d == expected  for d,expected in zip(data,expected_data) ])

    def test_pgfGenerator(self):
        """ Tests for the pgfGenerator strategy"""
        generator = PgfGenerator()

        old_types = self.plot_config.plot_types
        self.plot_config.plot_types = ["scatter","scatter"] #At the moment just scatter is implemented for pgf

        figures = self.getData(generator)

        pass #TODO: Currently not tested until tikzplotly is more robust.

        self.plot_config.plot_types = old_types




@pytest.mark.parametrize(("format","expected_class"),[
    ("plotly",PlotlyGenerator),
    ("html",PlotlyHtmlGenerator),
    ("pgf",PgfGenerator),
    ("csv",CsvGenerator),
    ("unkown",None)
])
def testDataGeneratorFactory(format,expected_class):
    """ Tests the correct generation of DataGeneratorStrategy objects by the DataGeneratorFactory class """
    if expected_class:
        strat = DataGeneratorFactory.create(format)
        assert isinstance(strat,expected_class)
        assert hasattr(strat,"generate") and callable(strat.generate)
    else:
        with pytest.raises(NotImplementedError):
            strat = DataGeneratorFactory.create(format)
