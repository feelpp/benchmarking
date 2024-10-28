from feelpp.benchmarking.report.machines.machine import Machine
from feelpp.benchmarking.report.base.repository import ModuleRepository

class MachineRepository(ModuleRepository):
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
        self.id = "machines"
        self.display_name = "Supercomputers"
        self.description = "EuroHPC ressources"

    def link(self, applications, use_cases, execution_mapping):
        """ Create the links between the machines and the applications and test cases depending on the execution mapping
        Will update the tree attribute of the machines, creating a dictionary of applications and test cases
        Args:
            applications (list[Application]): The list of applications
            use_cases (list[UseCase]): The list of test cases
            execution_mapping (dict): The execution mapping
        """
        for machine in self.data:
            for app_id, app_info in execution_mapping.items():
                application = applications.get(app_id)
                if machine.id not in app_info:
                    continue
                machine.tree[application] = {}
                for use_case_id in app_info[machine.id]["use_cases"]:
                    use_case = use_cases.get(use_case_id)
                    machine.tree[application][use_case] = []
