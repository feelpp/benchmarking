import os
from feelpp.benchmarking.report.components.baseComponent import BaseComponent

class Machine(BaseComponent):
    def __init__(self, id, display_name, description):
        super().__init__(id, display_name, description)

    def initModules(self, base_dir, renderer, parent_id = "supercomputers"):
        super().initModules(base_dir, renderer, parent_id, self_tag_id=self.id)

        for application, test_cases in self.tree.items():
            application.initModules(os.path.join(base_dir,self.id), renderer,parent_id = self.id, self_tag_id = f"{self.id}-{application.id}")
            for test_case in test_cases:
                test_case.initModules(os.path.join(base_dir,self.id,application.id), renderer, parent_id = f"{self.id}-{application.id}", self_tag_id = f"{self.id}-{application.id}-{test_case.id}")