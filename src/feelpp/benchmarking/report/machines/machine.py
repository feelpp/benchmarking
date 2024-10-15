from feelpp.benchmarking.report.base.baseComponent import BaseComponent
import os

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
        self.type = "machine"

    def createOverviews(self,base_dir, renderer):
        for application, keys in self.model_tree["children"].items():
            for use_case, overview_model in keys["children"].items():

                renderer.render(
                    os.path.join(base_dir,self.id,application.id,use_case.id,"overview.adoc"),
                    data = dict(
                        parent_catalogs = f"{self.id}-{application.id}-{use_case.id}",
                        reports_df = overview_model.master_df.to_dict(),
                        use_case = use_case,
                        machine = self,
                        application = application
                    )
                )
