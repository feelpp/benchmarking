import os

class Machine:
    def __init__(self, id, display_name, description):
        self.id = id
        self.display_name = display_name
        self.description = description

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

    def indexData(self):
        return dict(
            title = self.display_name,
            layout = "toolboxes",
            tags = f"catalog, toolbox, {self.id}",
            parent_catalogs = "supercomputers",
            description = self.description,
            illustration = f"ROOT:{self.id}.jpg"
        )