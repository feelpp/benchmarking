import numpy as np

class ResourceStrategy:
    """ Resource Strategy abstract class to configure the resources for the test """
    def configure(self, resources, rfm_test):
        """ Configure the resources for the test
        Args:
            resources (dict): The resources pydantic model
            rfm_test (ReframeTest): The ReFrame test to configure
        """
        raise NotImplementedError("The configure method should be implemented in the subclass")

    def validate(self, rfm_test):
        """ Validate the resources for the test
        Args:
            rfm_test (ReframeTest): The ReFrame test to validate
        """
        assert rfm_test.num_tasks > 0, 'Number of tasks should be greater than 0'

class TaskAndTaskPerNodeStrategy(ResourceStrategy):
    """ Resource Strategy to configure the resources for the test with tasks and tasks per node """
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks_per_node = int(resources.tasks_per_node)
        rfm_test.num_tasks = int(resources.tasks)

    def validate(self, rfm_test):
        super().validate(rfm_test)
        assert rfm_test.num_tasks % rfm_test.num_tasks_per_node == 0, 'Number of tasks should be divisible by tasks per node'
        assert rfm_test.num_tasks >= rfm_test.num_tasks_per_node > 0, 'Number of tasks should be greater than tasks per node'
        assert rfm_test.num_tasks_per_node <= rfm_test.current_partition.processor.num_cpus, f"A node has not enough capacity ({rfm_test.current_partition.processor.num_cpus}, {rfm_test.num_tasks_per_node})"

class NodesAndTasksPerNodeStrategy(ResourceStrategy):
    """ Resource Strategy to configure the resources for the test with nodes and tasks per node
        The number of tasks is calculated as the number of nodes multiplied by the number of tasks per node
    """
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks_per_node = int(resources.tasks_per_node)
        rfm_test.num_nodes = int(resources.nodes)
        rfm_test.num_tasks = rfm_test.num_tasks_per_node * rfm_test.num_nodes

    def validate(self, rfm_test):
        super().validate(rfm_test)
        assert rfm_test.num_tasks_per_node <= rfm_test.current_partition.processor.num_cpus, f"A node has not enough capacity ({rfm_test.current_partition.processor.num_cpus}, {rfm_test.num_tasks_per_node})"


class TasksAndNodesStrategy(ResourceStrategy):
    """ Resource Strategy to configure the resources for the test with tasks and nodes
        The number of tasks per node is calculated as the euclidean quotient of the number of tasks divided by the number of nodes
    """
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks = int(resources.tasks)
        rfm_test.num_nodes = int(resources.nodes)
        rfm_test.num_tasks_per_node = rfm_test.num_tasks // rfm_test.num_nodes

    def validate(self, rfm_test):
        super().validate(rfm_test)
        assert rfm_test.num_nodes > 0, "Number of Tasks and nodes should be strictly positive."
        assert rfm_test.num_nodes >= np.ceil(rfm_test.num_tasks/rfm_test.current_partition.processor.num_cpus), f"Cannot accomodate {rfm_test.num_tasks} tasks in {rfm_test.num_nodes} nodes"


class TasksStrategy(ResourceStrategy):
    """ Resource Strategy to configure the resources for the test with tasks
        The number of tasks per node is calculated as the minimum between the number of tasks and the number of CPUs per node
    """
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks = int(resources.tasks)
        rfm_test.num_tasks_per_node = min(rfm_test.num_tasks,rfm_test.current_partition.processor.num_cpus)


class MemoryEnforcer:
    """ Plugin to recompute resources based on the memory requirements
        The number of nodes is computed as the ceil of the euclidean quotient of the memory divided by the memory per node
        """
    def __init__(self, memory):
        """Args:
            memory (int): The total memory requirement that an application needs (in GB)
        """
        self.memory = int(memory)

    def enforceMemory(self, rfm_test):
        nodes = int(np.ceil(self.memory / rfm_test.current_partition.extras["memory_per_node"]))
        if not hasattr(rfm_test,"num_nodes"):
            rfm_test.num_nodes = nodes
        rfm_test.num_nodes = max(rfm_test.num_nodes,nodes)

        rfm_test.num_tasks_per_node = min(rfm_test.num_tasks_per_node, rfm_test.num_tasks // rfm_test.num_nodes)

class ExclusiveAccessEnforcer:
    """ Plugin to enforce exclusive access value to the nodes
        The exclusive access value is set to True by default
    """
    def __init__(self, exclusive_access):
        """Args:
            exclusive_access (bool): The exclusive access value
        """
        self.exclusive_access = bool(exclusive_access) if exclusive_access is not None else True

    def enforceExclusiveAccess(self, rfm_test):
        rfm_test.exclusive_access = self.exclusive_access

class ResourceHandler:
    """ Resource Handler to set the resources for the test, based on the resources model """
    @staticmethod
    def setResources(resources, rfm_test):
        """ Set the resources for the test based on the resources model and its combinations (tasks, tasks_per_node, nodes)
        If the memory is set, the number of nodes is recomputed to accomodate the memory requirements
        Args:
            resources (dict): The resources pydantic model
            rfm_test (ReframeTest): The ReFrame test to configure
        Returns:
            ReFrameTest: The ReFrame test with the resources configured
        """
        if resources.tasks and resources.tasks_per_node:
            strategy = TaskAndTaskPerNodeStrategy()
        elif resources.nodes and resources.tasks_per_node:
            strategy = NodesAndTasksPerNodeStrategy()
        elif resources.tasks and resources.nodes:
            raise NotImplementedError("Number of tasks and Nodes combination is not yet supported")
            strategy = TasksAndNodesStrategy()
        elif resources.tasks:
            strategy = TasksStrategy()
        else:
            raise ValueError("The Tasks parameter should contain either (tasks_per_node,nodes), (tasks,nodes), (tasks) or (tasks, tasks_per_node)")

        strategy.configure(resources, rfm_test)

        if resources.memory:
            MemoryEnforcer(resources.memory).enforceMemory(rfm_test)

        ExclusiveAccessEnforcer(resources.exclusive_access).enforceExclusiveAccess(rfm_test)

        strategy.validate(rfm_test)

        return rfm_test