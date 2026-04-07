import warnings
from feelpp.benchmarking.json_report.figures.plotly.plotlyFigures import *



class FigureFactory:
    """ Factory class to dispatch concrete figure elements"""

    @staticmethod
    def create(plot_type, plot_config) -> PlotlyFigure:
        """ Creates a concrete figure element
        Args:
            plot_config (Plot). Pydantic object with the plot configuration information
        """
        if plot_type in ["scatter","marked_scatter"]:
            fill_lines = ["optimal","half-optimal"] if plot_config.transformation=="speedup" else []

        if plot_type ==  "scatter":
            return PlotlyScatterFigure(plot_config, fill_lines)
        elif plot_type ==  "marked_scatter":
            return PlotlyMarkedScatter(plot_config, fill_lines)
        elif plot_type == "table":
            return PlotlyTableFigure(plot_config)
        elif plot_type == "stacked_bar":
            return PlotlyStackedBarFigure(plot_config)
        elif plot_type == "grouped_bar":
            return PlotlyGroupedBarFigure(plot_config)
        elif plot_type == "heatmap":
            return PlotlyHeatmapFigure(plot_config)
        elif plot_type == "sunburst":
            return PlotlySunburstFigure(plot_config)
        elif plot_type == "scatter3d":
            return PlotlyScatter3DFigure(plot_config)
        elif plot_type == "surface3d":
            return PlotlySurface3DFigure(plot_config)
        elif plot_type == "parallelcoordinates":
            return PlotlyParallelcoordinatesFigure(plot_config)
        else:
            warnings.warn(f"Figure type note implemented {plot_type}")
            return None