from feelpp.benchmarking.report.figureFactory import PlotlyFigureFactory, TikzFigureFactory
from feelpp.benchmarking.report.transformationFactory import TransformationStrategyFactory

import tempfile
import tikzplotly

class DataGenerator:
    def __init__(self):
        pass

    def generate(self,plots_config,master_df):
        """ Returns a list of data objects (depending on the chosen strategy) for each figure specified on the plot configuration, using the model master dataframe """
        raise NotImplementedError

class PlotlyGenerator(DataGenerator):
    def generate(self,plots_config,master_df):
        """ Creates plotly figures for each plot specified on the view config file
        Returns a list of plotly figures.
        """
        figures = []
        for plot_config in plots_config:
            for plot in PlotlyFigureFactory.create(plot_config):
                figures.append( plot.createFigure(master_df) )
        return figures

class PlotlyHtmlGenerator(PlotlyGenerator):
    def generate(self,plots_config,master_df):
        """ Creates plotly figures in html for each plot specified on the view config file
        Returns a list of plotly HTML figures
        """
        plotly_figures = super().generate(plots_config,master_df)
        return [fig.to_html() for fig in plotly_figures]

class PgfGenerator(PlotlyGenerator):
    def generate(self,plots_config,master_df):
        """ Creates PGF plots for each figure specified on the view config file
        """
        figures = []
        for plot_config in plots_config:
            for plot in TikzFigureFactory.create(plot_config):
                figures.append( plot.createTex(master_df) )
        return figures

class CsvGenerator(DataGenerator):
    def generate(self,plots_config,master_df):
        """ Create a list containing the data for each plot specified on the view config in CSV format.
        Returns (list[str]): List of csv data.
        """
        csvs = []
        for plot_config in plots_config:
            strategy = TransformationStrategyFactory.create(plot_config)
            csv_data = strategy.calculate(master_df).to_csv()
            for _ in plot_config.plot_types:
                csvs.append(csv_data)

        return csvs


class DataGeneratorFactory:
    @staticmethod
    def create(format):
        """ Creates the appropriate strategy based on the format """
        if format == "plotly":
            return PlotlyGenerator()
        elif format == "html":
            return PlotlyHtmlGenerator()
        elif format == "pgf":
            return PgfGenerator()
        elif format == "csv":
            return CsvGenerator()
        else:
            raise NotImplementedError
