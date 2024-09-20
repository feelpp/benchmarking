import os

class Application:
    def __init__(self, id, display_name, description):
        self.id = id
        self.display_name = display_name
        self.description = description

        self.machines = []
        self.test_cases = []


    def addMachine(self, machine):
        if machine not in self.machines:
            self.machines.append(machine)
            if self not in machine.applications:
                machine.addApplication(self)

    def addTestCase(self, test_case):
        if test_case not in self.test_cases:
            self.test_cases.append(test_case)
            if self != test_case.application:
                test_case.setApplication(self)

    def addAtomicReport(self, atomic_report):
        for test_case in self.test_cases:
            if test_case.id == atomic_report.test_case_id:
                test_case.addAtomicReport(atomic_report)

    def indexData(self):
        return dict(
            title = self.display_name,
            layout = "toolboxes",
            tags = f"catalog, toolbox, {self.parent.id}-{self.id}",
            parent_catalogs = self.parent.id,
            description = self.description,
            illustration = f"ROOT:{self.id}.jpg"
        )