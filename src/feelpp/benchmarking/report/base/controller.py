

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

    def generatePlotly(self):
        """ Creates plotly figures for each plot specified on the view config file
        Returns a list of plotly figures.
        """
        return [ figure.createFigure(self.model.master_df) for figure in self.view.figures ]

    def generatePlotlyHtml(self):
        """ Creates plotly figures in html for each plot specified on the view config file
        Returns a list of plotly HTML figures
        """
        return [ figure.createFigureHtml(self.model.master_df) for figure in self.view.figures ]

    def generateTikz(self):
        """ Creates Tikz/Pgf figures for each plot specified on the view config file
        Returns:
            list[str] LaTeX pgf plots.
        """
        return [ figure.createTex(self.model.master_df) for figure in self.view.figures ]

    def generateCsv(self):
        """ Create a list containing the data for each plot specified on the view config in CSV format.
        Returns (list[str]): List of csv data.
        """
        return [ figure.createTex(self.model.master_df) for figure in self.view.figures ]


    def generateData(self,format):
        """ Creates a list of data depending on the desired format, using the plot configuration and the model's master dataframe"""
        if format == "plotly":
            return self.generatePlotly()
        elif format == "html":
            return self.generatePlotlyHtml()
        elif format in ["tikz", "pgf"]:
            return self.generateTikz()
        elif format == "csv":
            return self.generateCsv()
        else:
            raise NotImplementedError