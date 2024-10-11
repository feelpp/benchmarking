import os
import pandas as pd
from feelpp.benchmarking.report.components.baseComponent import BaseComponent
from feelpp.benchmarking.report.components.figureFactory import FigureFactory
from feelpp.benchmarking.reframe.config.configSchemas import Plot

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

                output_folder_path = f"{base_dir}/{app.id}/{use_case.id}/{self.id}"

                if not os.path.exists(output_folder_path):
                    raise FileNotFoundError(f"The folder {output_folder_path} does not exist. Modules should be initialized beforehand ")

                renderer.render(
                    f"{output_folder_path}/overview.adoc",
                    dict(
                        reports_dfs = { report.date: report.model.master_df.to_dict(orient='dict') for report in reports },
                        plots_config = self.plots_config,
                        parent_catalogs = f"{app.id}-{use_case.id}-{self.id}",
                        application_display_name = app.display_name,
                        machine_display_name = self.display_name,
                        use_case_display_name = use_case.display_name
                    )
                )


class MachineModel:
    """ Model component of the useCase.
        This class holds the aggregated data for all atomic reports in a use case.
    """
    def __init__(self, atomic_models_dfs):
        self.master_df = self.buildMasterDf( atomic_models_dfs )

    def buildMasterDf(self,atomic_models_dfs):
        """ creates a dataframe holding all master dataframes from atomic reports.
            Facilitates pivoting and aggregation
        Args:
            atomic_models_dfs (dict[pd.DataFrame]). Dict with atomic report master dataframes (serialized with to_dict(orient='dict')), keys are report's start and end times as tuple
        """
        parsed_dfs = []
        for date, df in atomic_models_dfs.items():
            parsed_df = pd.DataFrame.from_records(df)
            parsed_df["time_start"] = date
            parsed_dfs.append(parsed_df)

        return pd.concat(parsed_dfs ,axis=0)



class MachineController:
    """ Controller component of the Machine component, it orchestrates the model with the view"""
    def __init__(self, model, view):
        """
        Args:
            model (MachineModel): The use case model component
            view (MachineView): The use case view component
        """
        self.model = model
        self.view = view

    def generateAll(self):
        """ Creates plotly figures for each plot specified on the view config file
        Returns a list of plotly figures.
        """
        #TODO: Can be a generator
        figs = []
        for plot_config in self.view.plots_config:
            for plot in FigureFactory.create(plot_config):
                figs.append(plot.createFigure(self.model.master_df))
        return figs


class MachineView:
    """ View component for the Machine Report, it contains all figure generation related code """
    def __init__(self,plots_config):
        """ parses the plots config. This JSON tells what plots to show and how to display them
        Args:
            plots_config (dict): Configuration on how to plot the values
        """
        self.plots_config = [Plot(**d) for d in plots_config]