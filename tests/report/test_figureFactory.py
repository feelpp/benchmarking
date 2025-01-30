from feelpp.benchmarking.report.figureFactory import PlotlyFigureFactory, PlotlyScatterFigure, PlotlyTableFigure, PlotlyStackedBarFigure, PlotlyGroupedBarFigure
from test_transformationFactory import PlotConfigMocker
import pytest



@pytest.mark.parametrize(("types","expected_classes"),[
    (["scatter"],[PlotlyScatterFigure]),
    (["scatter","table"],[PlotlyScatterFigure]),
    (["table"],[PlotlyTableFigure]),
    (["stacked_bar"],[PlotlyStackedBarFigure]),
    (["grouped_bar"],[PlotlyGroupedBarFigure]),
    (["unkown"],[])
])
def test_figureFactory(types,expected_classes):
    """ Tests the correct generation of Figure objects by the PlotlyFigureFactory class """
    plot_config = PlotConfigMocker(transformation="speedup",plot_types=types)
    if expected_classes:
        figures = PlotlyFigureFactory.create(plot_config)
        assert len(types) == len(figures)
        for figure,expected_class in zip(figures,expected_classes):
            assert isinstance(figure,expected_class)
            assert hasattr(figure,"createFigure") and callable(figure.createFigure)
    else:
        with pytest.raises(NotImplementedError):
            figures = PlotlyFigureFactory.create(plot_config)
