import os
from feelpp.benchmarking.report.component import Component

class Machine(Component):
    def __init__(self, id, display_name, description):
        super().__init__(id, display_name, description)
        self.applications = []
        self.test_cases = []

    def addApplication(self, application):
        if application not in self.applications:
            self.applications.append(application)
        if self not in application.machines:
            application.addMachine(self)

    def addTestCase(self, test_case):
        if test_case not in self.test_cases:
            self.test_cases.append(test_case)
        if self not in test_case.machines:
            test_case.addMachine(self)

    def initModules(self, base_dir, renderer, parent_id = "supercomputers"):
        super().initModules(base_dir, renderer, parent_id, self_tag_id=self.id)

        for application in self.applications:
            application.initModules(os.path.join(base_dir,self.id), renderer,parent_id = self.id, self_tag_id = f"{self.id}-{application.id}")
            for test_case in application.test_cases:
                test_case.initModules(os.path.join(base_dir,self.id,application.id), renderer, parent_id = f"{self.id}-{application.id}", self_tag_id = f"{self.id}-{application.id}-{test_case.id}")