from feelpp.benchmarking.report.figureFactory import FigureFactory
from feelpp.benchmarking.report.strategies import StrategyFactory

import tempfile
import tikzplotly

class Controller:
    """ Controller component , it orchestrates the model with the view"""
    def __init__(self, model, view):
        """
        Args:
            model (AtomicReportModel): The atomic report model component
            view (AtomicReportView): The atomic report view component
        """
        self.model = model
        self.view = view

    def generateFigures(self):
        """ Creates plotly figures in HTML for each plot specified on the view config file
        Returns a list of plotly figures.
        """
        figures = []
        for plot_config in self.view.plots_config:
            for plot in FigureFactory.create(plot_config):
                figures.append( plot.createFigure(self.model.master_df) )
        return figures

    def generateFiguresHtml(self):
        """ Creates plotly figures in html for each plot specified on the view config file
        Returns a list of plotly HTML figures """
        figures = self.generateFigures()
        return [fig.to_html() for fig in figures]

    def buildPgfs(self):
        figures = self.generateFigures()
        pgf_figures = []

        with tempfile.NamedTemporaryFile() as tmp_pgf_save:
            for figure in figures:
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


    def buildCsvs(self):
        """ Create a list containing the data for each plot specified on the view config in CSV format.
        Returns (list[str]): List of csv data.
        """
        csvs = []
        for plot_config in self.view.plots_config:
            strategy = StrategyFactory.create(plot_config)
            csv_data = strategy.calculate(self.model.master_df).to_csv()
            for _ in plot_config.plot_types:
                csvs.append(csv_data)

        return csvs