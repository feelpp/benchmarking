import os
from feelpp.benchmarking.report.components.baseComponent import BaseComponent

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

    def initModules(self, base_dir, renderer, parent_id = "supercomputers"):
        """ Initialize the modules for the component.
        Creates the directories recursively for the component and its children and renders the index.adoc files for each.

        Args:
            base_dir (str): The base directory for the modules
            renderer (Renderer): The renderer to use
            parent_id (str,optional): The catalog id of the parent component. Defaults to "supercomputers".
        """
        super().initModules(base_dir, renderer, parent_id, self_tag_id=self.id)

        for application, test_cases in self.tree.items():
            application.initModules(os.path.join(base_dir,self.id), renderer,parent_id = self.id, self_tag_id = f"{self.id}-{application.id}")
            for test_case in test_cases:
                test_case.initModules(os.path.join(base_dir,self.id,application.id), renderer, parent_id = f"{self.id}-{application.id}", self_tag_id = f"{self.id}-{application.id}-{test_case.id}")