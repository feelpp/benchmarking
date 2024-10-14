from feelpp.benchmarking.report.applications.application import Application
from feelpp.benchmarking.report.base.repository import Repository

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
        self.id = "applications"
        self.display_name = "Applications"
        self.description = "Applications [description TODO]"

    def link(self, machines, use_cases, execution_mapping):
        """ Create the links between the applications and the machines and test cases depending on the execution mapping
        Will update the tree attribute of the applications, creating a dictionary of machines and test cases
        Args:
            machines (list[Machine]): The list of machines
            use_cases (list[UseCase]): The list of test cases
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
