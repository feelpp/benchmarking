import os
from feelpp.benchmarking.report.component import Component

class TestCase(Component):
    def __init__(self, id, display_name, description):
        super().__init__(id, display_name, description)

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

    def addAtomicReport(self, atomic_report):
        if atomic_report not in self.atomic_reports:
            self.atomic_reports.append(atomic_report)
        if self != atomic_report.test_case:
            atomic_report.setTestCase(self)