from feelpp.benchmarking.report.component import Component
import os

class Application(Component):
    def __init__(self, id, display_name, description):
        super().__init__(id, display_name, description)

        self.machines = []
        self.test_cases = []
        self.atomic_reports = []


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
        if atomic_report not in self.atomic_reports:
            self.atomic_reports.append(atomic_report)
        if self != atomic_report.application:
            atomic_report.setApplication(self)
