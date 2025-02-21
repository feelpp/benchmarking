from feelpp.benchmarking.report.figures.figureFactory import FigureFactory, ScatterFigure, TableFigure, StackedBarFigure, GroupedBarFigure, HeatmapFigure
from test_transformationFactory import PlotConfigMocker
import pytest



@pytest.mark.parametrize(("types","expected_classes"),[
    (["scatter"],[ScatterFigure]),
    (["scatter","table"],[ScatterFigure]),
    (["table"],[TableFigure]),
    (["stacked_bar"],[StackedBarFigure]),
    (["grouped_bar"],[GroupedBarFigure]),
    (["heatmap"],[HeatmapFigure]),
    (["unkown"],[])
])
def test_figureFactory(types,expected_classes):
    """ Tests the correct generation of Figure objects by the FigureFactory class """
    plot_config = PlotConfigMocker(transformation="speedup",plot_types=types)
    if expected_classes:
        figures = FigureFactory.create(plot_config)
        assert len(types) == len(figures)
        for figure,expected_class in zip(figures,expected_classes):
            assert isinstance(figure,expected_class)
            assert hasattr(figure,"createFigure") and callable(figure.createFigure)
            assert hasattr(figure,"createTex") and callable(figure.createTex)
    else:
        with pytest.raises(NotImplementedError):
            figures = FigureFactory.create(plot_config)
