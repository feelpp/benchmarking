from feelpp.benchmarking.report.components.atomicReport import AtomicReport
from feelpp.benchmarking.report.components.application import Application
from feelpp.benchmarking.report.components.machine import Machine
from feelpp.benchmarking.report.components.testCase import TestCase


class Repository:
    """ Base class for repositories.
    Designed for containing and manipulating a unique list of items
    """
    def __init__(self):
        self.data = []

    def __iter__(self):
        """ Iterator for the repository """
        return iter(self.data)

    def add(self, item):
        """ Add an item to the repository, ensuring it is unique
        Args:
            item (object): The item to add
        """
        if item not in self.data:
            self.data.append(item)

    def printHierarchy(self):
        """ Print the hierarchy of the repository """
        for item in self.data:
            item.printHierarchy()

    def get(self, id):
        """ Get an item by its id """
        return next(filter(lambda x: x.id == id, self.data))

    def link(self, other_components, execution_mapping):
        """ Pure virtual function to link the items of the repository to other components.
         It will update the tree attribute of the items """
        pass

class MachineRepository(Repository):
    """ Repository for machines """
    def __init__(self, machines_json):
        """ Constructor for the MachineRepository class.
        Initializes the machines from the JSON data, uniquely
        Args:
            machines_json (dict): The JSON data for the machines
        """
        self.data:list[Machine] = [
            Machine(
                id = machine_id,
                display_name = machine_info["display_name"],
                description = machine_info["description"],
            )
            for machine_id, machine_info in machines_json.items()
    ]

    def link(self, applications, use_cases, execution_mapping):
        """ Create the links between the machines and the applications and test cases depending on the execution mapping
        Will update the tree attribute of the machines, creating a dictionary of applications and test cases
        Args:
            applications (list[Application]): The list of applications
            use_cases (list[TestCase]): The list of test cases
            execution_mapping (dict): The execution mapping
        """
        for machine in self.data:
            if machine.id not in execution_mapping:
                continue
            for app_id, app_info in execution_mapping[machine.id].items():
                application = next(filter(lambda a: a.id == app_id, applications))
                machine.tree[application] = {}
                for use_case_id in app_info["use_cases"]:
                    use_case = next(filter(lambda t: t.id == use_case_id and application in t.tree, use_cases))
                    machine.tree[application][use_case] = []

class ApplicationRepository(Repository):
    """ Repository for applications """
    def __init__(self, applications_json):
        """ Constructor for the ApplicationRepository class.
        Initializes the applications from the JSON data, uniquely
        Args:
            applications_json (dict): The JSON data for the applications
        """
        self.data:list[Application] = [
            Application(
                id = app_id,
                display_name = app_info["display_name"],
                description = app_info["description"],
            )
            for app_id, app_info in applications_json.items()
    ]

    def link(self, machines, use_cases, execution_mapping):
        """ Create the links between the applications and the machines and test cases depending on the execution mapping
        Will update the tree attribute of the applications, creating a dictionary of machines and test cases
        Args:
            machines (list[Machine]): The list of machines
            use_cases (list[TestCase]): The list of test cases
            execution_mapping (dict): The execution mapping
        """
        for application in self.data:
            for machine_id, machine_info in execution_mapping.items():
                if not application.id in machine_info:
                    continue
                machine = next(filter(lambda m: m.id == machine_id, machines))
                application.tree[machine] = {}
                for use_case_id in machine_info[application.id]["use_cases"]:
                    use_case = next(filter(lambda t: t.id == use_case_id and application in t.tree, use_cases))
                    application.tree[machine][use_case] = []

class TestCaseRepository(Repository):
    """ Repository for test cases """
    def __init__(self, applications_json, applications):
        """ Constructor for the TestCaseRepository class.
        Initializes the test cases from the JSON data, uniquely.
        A test case is strictly linked to a single application
        Args:
            applications_json (dict): The JSON data for the applications
            applications (list[Application]): The list of applications
        """
        self.data:list[TestCase] = []
        for app_id, app_info in applications_json.items():
            application = next(filter(lambda a: a.id == app_id, applications))
            for use_case, use_case_info in app_info["use_cases"].items():
                self.add(
                    TestCase(
                        id = use_case,
                        display_name = use_case_info["display_name"],
                        description = use_case_info["description"],
                        application = application
                    )
                )

    def link(self, applications, machines, execution_mapping):
        """ Create the links between the test cases and the applications and machines depending on the execution mapping
        Will update the tree attribute of the test cases, creating a dictionary of applications and machines
        The tree attribute contains a single application on the base level
        Args:
            applications (list[Application]): The list of applications
            machines (list[Machine]): The list of machines
            execution_mapping (dict): The execution mapping
        """
        for use_case in self.data:
            for machine_id, machine_info in execution_mapping.items():
                machine = next(filter(lambda m: m.id == machine_id, machines))
                for app_id, app_info in machine_info.items():
                    if not use_case.id in app_info["use_cases"]:
                        continue
                    application = next(filter(lambda a: a.id == app_id, applications))
                    if not application in use_case.tree:
                        continue
                    use_case.tree[application][machine] = []


class AtomicReportRepository(Repository):
    """ Repository for atomic reports """
    def __init__(self, benchmarking_config_json, download_handler):
        """ Constructor for the AtomicReportRepository class.
        Initializes the atomic reports from the benchmarking config JSON data
        after Downloading the reports using a download handler
        Args:
            benchmarking_config_json (dict): The benchmarking config JSON data
            download_handler (GirderHandler): The GirderHandler object to download the reports
        """
        self.data:list[AtomicReport] = []
        self.downloadAndInitAtomicReports(benchmarking_config_json, download_handler)

    def downloadAndInitAtomicReports(self,benchmarking_config_json, download_handler):
        """ Download the reports and initialize the atomic reports
        Args:
            benchmarking_config_json (dict): The benchmarking config JSON data
            download_handler (GirderHandler): The GirderHandler object to download the reports
        """
        for machine_id, machine_info in benchmarking_config_json.items():
            for app_id, app_info in machine_info.items():
                json_filenames = download_handler.downloadFolder(app_info["girder_folder_id"], output_dir=f"{machine_id}/{app_id}")
                possible_use_cases = app_info["use_cases"]
                for json_file in json_filenames:
                    json_file = f"{download_handler.download_base_dir}/{machine_id}/{app_id}/{json_file}"
                    self.add(
                        AtomicReport(
                            application_id = app_id,
                            machine_id = machine_id,
                            json_file = json_file,
                            possible_use_cases = possible_use_cases
                        )
                    )

    def link(self, applications, machines, use_cases):
        """ Create the links between the atomic reports and the applications, machines and test cases
        An atomic report is identified by a single application, machine and test case
        the report is added to the respective tree of the application, machine and test case
        Args:
            applications (list[Application]): The list of applications
            machines (list[Machine]): The list of machines
            use_cases (list[TestCase]): The list of test cases
        """
        for atomic_report in self.data:
            application = next(filter(lambda a: a.id == atomic_report.application_id, applications))
            machine = next(filter(lambda m: m.id == atomic_report.machine_id, machines))
            use_case = next(filter(lambda t: t.id == atomic_report.use_case_id and application in t.tree and machine in t.tree[application], use_cases))

            atomic_report.setIndexes(application, machine, use_case)


            machine.tree[application][use_case].append(atomic_report)
            application.tree[machine][use_case].append(atomic_report)
            use_case.tree[application][machine].append(atomic_report)