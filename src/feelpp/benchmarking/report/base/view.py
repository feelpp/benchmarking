from feelpp.benchmarking.reframe.config.configSchemas import Plot

class View:
    """ Abstract view component"""
    def __init__(self,plots_config):
        """ Parses the plots config list. This JSON tells what plots to show and how to display them
        Args:
            plots_config list[dict]. List with dictionaries specifying plots configuration.
        """
        self.plots_config = [Plot(**d) for d in plots_config]
