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

    def initModules(self, base_dir, renderer, parent_id = "catalog-index"):
        for item in self.data:
            item.initModules(base_dir, renderer, parent_id)

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
            for app_id, app_info in execution_mapping.items():
                application = next(filter(lambda a: a.id == app_id, applications))
                if machine.id not in app_info:
                    continue
                machine.tree[application] = {}
                for use_case_id in app_info[machine.id]["use_cases"]:
                    use_case = next(filter(lambda t: t.id == use_case_id, use_cases))
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
            if not application.id in execution_mapping:
                continue
            for machine_id, machine_info in execution_mapping[application.id].items():
                machine = next(filter(lambda m: m.id == machine_id, machines))
                for use_case_id in machine_info["use_cases"]:
                    use_case = next(filter(lambda t: t.id == use_case_id, use_cases))
                    if use_case not in application.tree:
                        application.tree[use_case] = {}
                    application.tree[use_case][machine] = []

class TestCaseRepository(Repository):
    """ Repository for test cases """
    def __init__(self, use_cases_json):
        """ Constructor for the TestCaseRepository class.
        Initializes the test cases from the JSON data, uniquely.
        Args:
            use_cases_json (dict): The JSON metadata for the test cases
        """
        self.data:list[TestCase] = [
            TestCase(
                id = use_case_id,
                display_name = use_case_info["display_name"],
                description = use_case_info["description"]
            )
            for use_case_id, use_case_info in use_cases_json.items()
        ]

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
            for app_id, app_info in execution_mapping.items():
                application = next(filter(lambda a: a.id == app_id, applications))
                use_case.tree[application] = {}
                for machine_id, machine_info  in app_info.items():
                    machine = next(filter(lambda m: m.id == machine_id, machines))
                    if not use_case.id in machine_info["use_cases"]:
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
        for app_id, app_info in benchmarking_config_json.items():
            for machine_id, machine_info in app_info.items():
                outdir = f"{app_id}/{machine_id}"
                json_filenames = download_handler.downloadFolder(machine_info["girder_folder_id"], output_dir=outdir)
                possible_use_cases = machine_info["use_cases"]
                for json_file in json_filenames:
                    json_file = f"{download_handler.download_base_dir}/{outdir}/{json_file}"
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
            application.tree[use_case][machine].append(atomic_report)
            use_case.tree[application][machine].append(atomic_report)