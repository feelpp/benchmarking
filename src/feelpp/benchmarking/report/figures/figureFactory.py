from feelpp.benchmarking.report.transformationFactory import TransformationStrategyFactory

from feelpp.benchmarking.report.figures.base import CompositeFigure
from feelpp.benchmarking.report.figures.tikzFigures import TikzFigure, TikzScatterFigure, TikzGroupedBarFigure, TikzStackedBarFigure, TikzTableFigure
from feelpp.benchmarking.report.figures.plotlyFigures import PlotlyFigure, PlotlyScatterFigure, PlotlyGroupedBarFigure, PlotlyStackedBarFigure, PlotlyTableFigure, PlotlyHeatmapFigure, PlotlySunburstFigure, PlotlyScatter3DFigure, PlotlySurface3DFigure, PlotlyParallelcoordinatesFigure



class ScatterFigure(CompositeFigure):
    """ Composite figure class for scatter figures"""
    def __init__(self, plot_config, transformation_strategy, fill_lines=[]):
        self.plotly_figure = PlotlyScatterFigure(plot_config,transformation_strategy,fill_lines)
        self.tikz_figure = TikzScatterFigure(plot_config,transformation_strategy,fill_lines)

class TableFigure(CompositeFigure):
    """ Composite figure class for table figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlyTableFigure(plot_config,transformation_strategy)
        self.tikz_figure = TikzTableFigure(plot_config,transformation_strategy)

class StackedBarFigure(CompositeFigure):
    """ Composite figure class for stacked bar figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlyStackedBarFigure(plot_config,transformation_strategy)
        self.tikz_figure = TikzStackedBarFigure(plot_config,transformation_strategy)

class GroupedBarFigure(CompositeFigure):
    """ Composite figure class for grouped bar figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlyGroupedBarFigure(plot_config,transformation_strategy)
        self.tikz_figure = TikzGroupedBarFigure(plot_config,transformation_strategy)

class HeatmapFigure(CompositeFigure):
    """ Composite figure class for heatmap figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlyHeatmapFigure(plot_config,transformation_strategy)
        self.tikz_figure = None

class SunburstFigure(CompositeFigure):
    """ Composite figure class for sunburst figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlySunburstFigure(plot_config,transformation_strategy)
        self.tikz_figure = None

class Scatter3DFigure(CompositeFigure):
    """ Composite figure class for 3D scatter figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlyScatter3DFigure(plot_config,transformation_strategy)
        self.tikz_figure = None

class Surface3DFigure(CompositeFigure):
    """ Composite figure class for 3D surface figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlySurface3DFigure(plot_config,transformation_strategy)
        self.tikz_figure = None

class ParallelcoordinatesFigure(CompositeFigure):
    """ Composite figure class for parallel coordinates figures"""
    def __init__(self, plot_config, transformation_strategy):
        self.plotly_figure = PlotlyParallelcoordinatesFigure(plot_config,transformation_strategy)
        self.tikz_figure = None

class FigureFactory:
    """ Factory class to dispatch concrete figure elements"""
    @staticmethod
    def create(plot_config):
        """ Creates a concrete composite figure element
        Args:
            plot_config (Plot). Pydantic object with the plot configuration information
        """
        strategy = TransformationStrategyFactory.create(plot_config)
        figures = []
        for plot_type in plot_config.plot_types:
            if plot_type ==  "scatter":
                fill_lines = []
                if plot_config.transformation=="speedup":
                    fill_lines = ["optimal","half-optimal"]
                figures.append(ScatterFigure(plot_config,strategy, fill_lines))
            elif plot_type == "table":
                figures.append(TableFigure(plot_config,strategy))
            elif plot_type == "stacked_bar":
                figures.append(StackedBarFigure(plot_config,strategy))
            elif plot_type == "grouped_bar":
                figures.append(GroupedBarFigure(plot_config,strategy))
            elif plot_type == "heatmap":
                figures.append(HeatmapFigure(plot_config,strategy))
            elif plot_type == "sunburst":
                figures.append(SunburstFigure(plot_config,strategy))
            elif plot_type == "scatter3d":
                figures.append(Scatter3DFigure(plot_config,strategy))
            elif plot_type == "surface3d":
                figures.append(Surface3DFigure(plot_config,strategy))
            elif plot_type == "parallelcoordinates":
                figures.append(ParallelcoordinatesFigure(plot_config,strategy))
            else:
                raise NotImplementedError

        return figures