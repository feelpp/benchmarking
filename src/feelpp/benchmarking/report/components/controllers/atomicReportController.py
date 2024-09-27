class AtomicReportController:
    """ Controller component of the Atomic Report, it orchestrates the model with the view"""
    def __init__(self, model, view):
        """
        Args:
            model (AtomicReportModel): The atomic report model component
            view (AtomicReportView): The atomic report view component
        """
        self.model = model
        self.view = view

    def generatePerformancePlot(self, strategy):
        """ Create multi-line scatter plot representing the performance of a test by stage or phases in a stage.
        Args:
            strategy (MetricStrategy): The strategy used for metric extraction
        """
        data = self.model.getDataForMetric(strategy)
        return self.view.plotScatters(data,title="Performance",yaxis_label="s")

    def generatePerformanceTable(self, strategy):
        """Create a plotly table for performance
        Args:
            strategy (MetricStrategy): The strategy used for metric extraction
        """
        data = self.model.getDataForMetric(strategy)
        return self.view.plotTable(data)

    def generateSpeedupPlot(self, strategy):
        """ Create multi-line scatter plot representing the performance of a test by stage or phases in a stage.
        Args:
            strategy (MetricStrategy): The strategy used for metric extraction
        """
        data = self.model.getDataForMetric(strategy)
        return self.view.plotSpeedup(data,title="Speedup")

    def generateSpeedupTable(self, strategy):
        """Create a plotly table for speedup
        Args:
            strategy (MetricStrategy): The strategy used for metric extraction
        """
        data = self.model.getDataForMetric(strategy)
        return self.view.plotSpeedupTable(data)

