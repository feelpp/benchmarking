import os
from feelpp.benchmarking.report.components.baseComponent import BaseComponent
from feelpp.benchmarking.report.components.models import MachineModel

class Machine(BaseComponent):
    """ Class representing a machine module/component.
    Inherits from BaseComponent.
    Should be used to store information related to benchmarks of a machine.
    """
    def __init__(self, id, display_name, description):
        """ Constructor for the Machine class
        Args:
            id (str): The id of the machine
            display_name (str): The display name of the machine
            description (str): The description of the machine
        """
        super().__init__(id, display_name, description)

        self.plots_config = [
            {
                "title": "Application performance over time",
                "plot_types": [
                    "scatter"
                ],
                "transformation": "performance_sum",
                "variables": [
                    "ElectricConstructor_init",
                    "ElectricPostProcessing_exportResults",
                    "ElectricSolve_solve"
                ],
                "names": [
                    "Application Performance"
                ],
                "xaxis": {
                    "parameter": "time_start",
                    "label": "Date"
                },
                "secondary_axis": {
                    "parameter": "hsize",
                    "label": "h size"
                },
                "yaxis": {
                    "label": "Execution time (s)"
                },
                "color_axis":{
                    "parameter": "nb_tasks",
                    "label": "Tasks"
                }
            }
        ]

    def createOverview(self, base_dir, renderer):
        """ Create the overview for an app-machine-usecase combination, from aggregating atomic report data
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """
        for app, use_cases in self.tree.items():
            for use_case, reports in use_cases.items():
                super().createOverview(
                    os.path.join(base_dir,app.id,use_case.id),
                    renderer,
                    data = dict(
                        reports_dfs = { report.date: report.model.master_df.to_dict(orient='dict') for report in reports },
                        plots_config = self.plots_config,
                        parent_catalogs = f"{app.id}-{use_case.id}-{self.id}",
                        application_display_name = app.display_name,
                        machine_display_name = self.display_name,
                        use_case_display_name = use_case.display_name
                    )
                )