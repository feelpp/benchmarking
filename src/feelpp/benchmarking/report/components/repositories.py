from feelpp.benchmarking.report.components.atomicReport import AtomicReport
from feelpp.benchmarking.report.components.application import Application
from feelpp.benchmarking.report.components.machine import Machine
from feelpp.benchmarking.report.components.testCase import TestCase


class Repository:
    def __init__(self):
        pass

    #Iterator
    def __iter__(self):
        return iter(self.data)

    def add(self, item):
        if item not in self.data:
            self.data.append(item)

    def printHierarchy(self):
        for item in self.data:
            item.printHierarchy()

    def get(self, id):
        return next(filter(lambda x: x.id == id, self.data))

class MachineRepository(Repository):
    def __init__(self, machines_json):
        self.data:list[Machine] = [
            Machine(
                id = machine_id,
                display_name = machine_info["display_name"],
                description = machine_info["description"],
            )
            for machine_id, machine_info in machines_json.items()
    ]

    def link(self, applications, test_cases, execution_mapping):
        for machine in self.data:
            if machine.id not in execution_mapping:
                continue
            for app_id, app_info in execution_mapping[machine.id].items():
                application = next(filter(lambda a: a.id == app_id, applications))
                machine.tree[application] = {}
                for test_case_id in app_info["test_cases"]:
                    test_case = next(filter(lambda t: t.id == test_case_id and application in t.tree, test_cases))
                    machine.tree[application][test_case] = []

class ApplicationRepository(Repository):
    def __init__(self, applications_json):
        self.data:list[Application] = [
            Application(
                id = app_id,
                display_name = app_info["display_name"],
                description = app_info["description"],
            )
            for app_id, app_info in applications_json.items()
    ]

    def link(self, machines, test_cases, execution_mapping):
        for application in self.data:
            for machine_id, machine_info in execution_mapping.items():
                if not application.id in machine_info:
                    continue
                machine = next(filter(lambda m: m.id == machine_id, machines))
                application.tree[machine] = {}
                for test_case_id in machine_info[application.id]["test_cases"]:
                    test_case = next(filter(lambda t: t.id == test_case_id and application in t.tree, test_cases))
                    application.tree[machine][test_case] = []

class TestCaseRepository(Repository):
    def __init__(self, applications_json, applications):
        self.data:list[TestCase] = []
        for app_id, app_info in applications_json.items():
            application = next(filter(lambda a: a.id == app_id, applications))
            for test_case, test_case_info in app_info["test_cases"].items():
                self.add(
                    TestCase(
                        id = test_case,
                        display_name = test_case_info["display_name"],
                        description = test_case_info["description"],
                        application = application
                    )
                )

    def link(self, applications, machines, execution_mapping):
        for test_case in self.data:
            for machine_id, machine_info in execution_mapping.items():
                machine = next(filter(lambda m: m.id == machine_id, machines))
                for app_id, app_info in machine_info.items():
                    if not test_case.id in app_info["test_cases"]:
                        continue
                    application = next(filter(lambda a: a.id == app_id, applications))
                    if not application in test_case.tree:
                        continue
                    test_case.tree[application][machine] = []


class AtomicReportRepository(Repository):
    def __init__(self, benchmarking_config_json, download_handler):
        self.data:list[AtomicReport] = []
        self.downloadAndInitAtomicReports(benchmarking_config_json, download_handler)

    def downloadAndInitAtomicReports(self,benchmarking_config_json, download_handler):
        for machine_id, machine_info in benchmarking_config_json.items():
            for app_id, app_info in machine_info.items():
                json_filenames = download_handler.downloadFolder(app_info["girder_folder_id"], output_dir=f"{machine_id}/{app_id}")
                possible_test_cases = app_info["test_cases"]
                for json_file in json_filenames:
                    json_file = f"{download_handler.download_base_dir}/{machine_id}/{app_id}/{json_file}"
                    self.add(
                        AtomicReport(
                            application_id = app_id,
                            machine_id = machine_id,
                            json_file = json_file,
                            possible_test_cases = possible_test_cases
                        )
                    )

    def link(self, applications, machines, test_cases):
        for atomic_report in self.data:
            application = next(filter(lambda a: a.id == atomic_report.application_id, applications))
            machine = next(filter(lambda m: m.id == atomic_report.machine_id, machines))
            test_case = next(filter(lambda t: t.id == atomic_report.test_case_id and application in t.tree and machine in t.tree[application], test_cases))

            atomic_report.setIndexes(application, machine, test_case)


            machine.tree[application][test_case].append(atomic_report)
            application.tree[machine][test_case].append(atomic_report)
            test_case.tree[application][machine].append(atomic_report)