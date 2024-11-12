from feelpp.benchmarking.report.figureFactory import FigureFactory

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

    def generateAll(self):
        """ Creates plotly figures for each plot specified on the view config file
        Returns a list of plotly figures.
        """
        for plot_config in self.view.plots_config:
            for plot in FigureFactory.create(plot_config):
                yield plot.createFigure(self.model.master_df)
