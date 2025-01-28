from feelpp.benchmarking.report.figureFactory import PlotlyFigureFactory, ScatterFigure, TableFigure, StackedBarFigure, GroupedBarFigure
from test_transformationFactory import PlotConfigMocker
import pytest



@pytest.mark.parametrize(("types","expected_classes"),[
    (["scatter"],[ScatterFigure]),
    (["scatter","table"],[ScatterFigure]),
    (["table"],[TableFigure]),
    (["stacked_bar"],[StackedBarFigure]),
    (["grouped_bar"],[GroupedBarFigure]),
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
