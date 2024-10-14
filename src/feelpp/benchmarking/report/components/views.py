from feelpp.benchmarking.reframe.config.configSchemas import Plot

class View:
    """ Abstract view component"""
    def __init__(self,plots_config):
        """ Parses the plots config list. This JSON tells what plots to show and how to display them
        Args:
            plots_config list[dict]. List with dictionaries specifying plots configuration.
        """
        self.plots_config = [Plot(**d) for d in plots_config]


class AtomicReportView(View):
    pass


class OverviewView(View):
    def __init__(self):
        plots_config = [
            {
                "title": "Application performance over time",
                "plot_types": ["scatter" ],
                "transformation": "performance_sum",
                "variables": [ "ElectricConstructor_init", "ElectricPostProcessing_exportResults", "ElectricSolve_solve" ],
                "names": [ "Application Performance" ],
                "xaxis": { "parameter": "time_start", "label": "Date" },
                "secondary_axis": { "parameter": "hsize", "label": "h size" },
                "yaxis": { "label": "Execution time (s)" },
                "color_axis":{ "parameter": "nb_tasks", "label": "Tasks" }
            }
        ]
        super().__init__(plots_config)