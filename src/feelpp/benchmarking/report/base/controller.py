from feelpp.benchmarking.report.figureFactory import FigureFactory
from feelpp.benchmarking.report.strategies import StrategyFactory

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
        figures = self.generateFigures()
        return [fig.to_html() for fig in figures]


    def buildCsvs(self):
        """
        """
        csvs = []
        for plot_config in self.view.plots_config:
            strategy = StrategyFactory.create(plot_config)
            csv_data = strategy.calculate(self.model.master_df).to_csv()
            csvs.append(csv_data)

        return "<br>".join(csvs)