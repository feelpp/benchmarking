import os
from feelpp.benchmarking.report.components.baseComponent import BaseComponent

class UseCase(BaseComponent):
    """ Class representing a test case module/component.
    Inherits from BaseComponent.
    Should be used to store information related to benchmarks of a test case.
    """
    def __init__(self, id, display_name, description):
        """ Constructor for the UseCase class
        tree attribute should contain only ONE application

        Args:
            id (str): The id of the test case
            display_name (str): The display name of the test case
            description (str): The description of the test case
        """
        super().__init__(id, display_name, description)


    def createOverview(self, base_dir, renderer):
        """ Create the overview for an app-usecase combination, from aggregating atomic report data
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """

        for app, machines in self.tree.items():

                output_folder_path = f"{base_dir}/{app.id}/{self.id}"

                if not os.path.exists(output_folder_path):
                    raise FileNotFoundError(f"The folder {output_folder_path} does not exist. Modules should be initialized beforehand ")

                renderer.render(
                    f"{output_folder_path}/overview.adoc",
                    dict(
                        parent_catalogs = f"{app.id}-{self.id}",
                        application_display_name = app.display_name,
                        use_case_display_name = self.display_name
                    )
                )