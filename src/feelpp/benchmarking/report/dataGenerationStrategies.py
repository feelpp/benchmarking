from feelpp.benchmarking.report.figureFactory import FigureFactory
from feelpp.benchmarking.report.transformationStrategies import StrategyFactory

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
            for plot in FigureFactory.create(plot_config):
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
        Returns a list of strings contianing LaTeX code defining the figures using PGF/TikZ
        """
        plotly_figures = super().generate(plots_config,master_df)
        pgf_figures = []
        with tempfile.NamedTemporaryFile() as tmp_pgf_save:
            for figure in plotly_figures:
                if figure.frames:
                    animation_pgf = []
                    for frame in figure.frames:
                        tikzplotly.save(tmp_pgf_save.name,frame)

                        with open(tmp_pgf_save.name) as tmp:
                            animation_pgf.append(tmp.read())
                    pgf_figures.append("\n\n".join(animation_pgf))
                else:
                    try:
                        tikzplotly.save(tmp_pgf_save.name,figure)
                    except IndexError as e:
                        print(e)
                        pgf_figures.append("")
                    else:
                        with open(tmp_pgf_save.name) as tmp:
                            pgf_figures.append(tmp.read())
        return pgf_figures

class CsvGenerator(DataGenerator):
    def generate(self,plots_config,master_df):
        """ Create a list containing the data for each plot specified on the view config in CSV format.
        Returns (list[str]): List of csv data.
        """
        csvs = []
        for plot_config in plots_config:
            strategy = StrategyFactory.create(plot_config)
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
