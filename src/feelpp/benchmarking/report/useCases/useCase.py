from feelpp.benchmarking.report.base.baseComponent import BaseComponent
import os

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
        self.type = "use_case"

    def createOverviews(self,base_dir, renderer):
        for application, keys in self.model_tree["children"].items():
            for machine, overview_model in keys["children"].items():

                renderer.render(
                    os.path.join(base_dir,self.id,application.id,machine.id,"overview.adoc"),
                    data = dict(
                        parent_catalogs = f"{self.id}-{application.id}-{machine.id}",
                        reports_df = overview_model.master_df.to_dict(),
                        use_case = self,
                        machine = machine,
                        application = application
                    )
                )