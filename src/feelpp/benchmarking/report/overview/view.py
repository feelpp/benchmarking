from feelpp.benchmarking.report.base.view import View

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