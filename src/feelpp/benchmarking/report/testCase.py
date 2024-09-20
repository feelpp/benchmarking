import os

class TestCase:
    def __init__(self, id, display_name, description):
        self.id = id
        self.display_name = display_name
        self.description = description

        self.application = None
        self.machines = []
        self.atomic_reports = []

    def setApplication(self, application):
        self.application = application
        if self not in application.test_cases:
            application.addTestCase(self)

    def addMachine(self, machine):
        if machine not in self.machines:
            self.machines.append(machine)
        if self not in machine.test_cases:
            machine.addTestCase(self)


    def indexData(self):
        return dict(
            title = self.display_name,
            layout = "toolboxes",
            tags = f"catalog, toolbox, {self.parent.parent.id}-{self.parent.id}-{self.id}",
            parent_catalogs = f"{self.parent.parent.id}-{self.parent.id}",
            description = self.description,
            illustration = f"ROOT:{self.id}.jpg"
        )
