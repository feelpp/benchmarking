from feelpp.benchmarking.reframe.config.configSchemas import Plot
from feelpp.benchmarking.report.figures.figureFactory import FigureFactory

class View:
    """ Abstract view component"""
    def __init__(self,plots_config):
        """ Parses the plots config list. This JSON tells what plots to show and how to display them
        Args:
            plots_config list[dict]. List with dictionaries specifying plots configuration.
        """
        self.plots_config = [Plot(**d) for d in plots_config]
        self.figures = [FigureFactory.create(plot_config) for plot_config in self.plots_config]