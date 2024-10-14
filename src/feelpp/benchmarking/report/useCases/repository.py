from feelpp.benchmarking.report.useCases.useCase import UseCase
from feelpp.benchmarking.report.base.repository import ModuleRepository

class UseCaseRepository(ModuleRepository):
    """ Repository for test cases """
    def __init__(self, use_cases_json):
        """ Constructor for the UseCaseRepository class.
        Initializes the test cases from the JSON data, uniquely.
        Args:
            use_cases_json (dict): The JSON metadata for the test cases
        """
        self.data:list[UseCase] = [
            UseCase(
                id = use_case_id,
                display_name = use_case_info["display_name"],
                description = use_case_info["description"]
            )
            for use_case_id, use_case_info in use_cases_json.items()
        ]
        self.id = "use_cases"
        self.display_name = "Use Cases"
        self.description = "Use cases for available applications"

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
                application = applications.get(app_id)
                use_case.tree[application] = {}
                for machine_id, machine_info  in app_info.items():
                    machine = machines.get(machine_id)
                    if not use_case.id in machine_info["use_cases"]:
                        continue
                    use_case.tree[application][machine] = []
                if use_case.tree[application] == {}:
                    del use_case.tree[application]


