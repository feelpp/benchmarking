from feelpp.benchmarking.report.dataGenerationStrategies import DataGeneratorFactory
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

    def generateData(self,format):
        """ Creates a list of data depending on the desired format, using the plot configuration and the model's master dataframe"""
        return DataGeneratorFactory.create(format).generate(self.view.plots_config,self.model.master_df)