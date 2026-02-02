import warnings
from feelpp.benchmarking.json_report.figures.tikz.tikzFigures import TikzFigure, TikzScatterFigure, TikzGroupedBarFigure, TikzStackedBarFigure, TikzTableFigure

class FigureFactory:
    """ Factory class to dispatch concrete figure elements"""
    @staticmethod
    def create(plot_type,plot_config) -> TikzFigure:
        """ Creates a concrete figure element
        Args:
            plot_config (Plot). Pydantic object with the plot configuration information
        """
        if plot_type in ["scatter","marked_scatter"]:
            fill_lines = ["optimal","half-optimal"] if plot_config.transformation=="speedup" else []

        if plot_type ==  "scatter":
            return TikzScatterFigure(plot_config, fill_lines)
        elif plot_type == "table":
            return TikzTableFigure(plot_config)
        elif plot_type == "stacked_bar":
            return TikzStackedBarFigure(plot_config)
        elif plot_type == "grouped_bar":
            return TikzGroupedBarFigure(plot_config)
        else:
            warnings.warn(f"Figure type note implemented {plot_type}")
            return None