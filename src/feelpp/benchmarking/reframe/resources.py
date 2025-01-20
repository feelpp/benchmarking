import numpy as np

class ResourceStrategy:
    def configure(self, resources, rfm_test):
        pass

    def validate(self, rfm_test):
        assert rfm_test.num_tasks > 0, 'Number of tasks should be greater than 0'

class TaskAndTaskPerNodeStrategy(ResourceStrategy):
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks_per_node = int(resources.tasks_per_node)
        rfm_test.num_tasks = int(resources.tasks)

    def validate(self, rfm_test):
        super().validate(rfm_test)
        assert rfm_test.num_tasks % rfm_test.num_tasks_per_node == 0, 'Number of tasks should be divisible by tasks per node'
        assert rfm_test.num_tasks >= rfm_test.num_tasks_per_node > 0, 'Number of tasks should be greater than tasks per node'
        assert rfm_test.num_tasks_per_node <= rfm_test.current_partition.processor.num_cpus, f"A node has not enough capacity ({rfm_test.current_partition.processor.num_cpus}, {rfm_test.num_tasks_per_node})"

class NodesAndTasksPerNodeStrategy(ResourceStrategy):
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks_per_node = int(resources.tasks_per_node)
        rfm_test.num_nodes = int(resources.nodes)
        rfm_test.num_tasks = rfm_test.num_tasks_per_node * rfm_test.num_nodes

    def validate(self, rfm_test):
        super().validate(rfm_test)
        assert rfm_test.num_tasks_per_node <= rfm_test.current_partition.processor.num_cpus, f"A node has not enough capacity ({rfm_test.current_partition.processor.num_cpus}, {rfm_test.num_tasks_per_node})"


class TasksAndNodesStrategy(ResourceStrategy):
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks = int(resources.tasks)
        rfm_test.num_nodes = int(resources.nodes)
        rfm_test.num_tasks_per_node = rfm_test.num_tasks // rfm_test.num_nodes

    def validate(self, rfm_test):
        super().validate(rfm_test)
        assert rfm_test.num_nodes > 0, "Number of Tasks and nodes should be strictly positive."
        assert rfm_test.num_nodes >= np.ceil(rfm_test.num_tasks/rfm_test.current_partition.processor.num_cpus), f"Cannot accomodate {rfm_test.num_tasks} tasks in {rfm_test.num_nodes} nodes"


class TasksStrategy(ResourceStrategy):
    def configure(self, resources, rfm_test):
        rfm_test.num_tasks = int(resources.tasks)
        rfm_test.num_tasks_per_node = min(rfm_test.num_tasks,rfm_test.current_partition.processor.num_cpus)


class MemoryEnforcer:
    def __init__(self, memory):
        self.memory = int(memory)

    def enforceMemory(self, rfm_test):
        nodes = int(np.ceil(self.memory / rfm_test.current_partition.extras["memory_per_node"]))
        if not hasattr(rfm_test,"num_nodes"):
            rfm_test.num_nodes = nodes
        rfm_test.num_nodes = max(rfm_test.num_nodes,nodes)

        rfm_test.num_tasks_per_node = min(rfm_test.num_tasks_per_node, rfm_test.num_tasks // rfm_test.num_nodes)

class ExclusiveAccessEnforcer:
    def __init__(self, exclusive_access):
        self.exclusive_access = bool(exclusive_access) if exclusive_access is not None else True

    def enforceExclusiveAccess(self, rfm_test):
        rfm_test.exclusive_access = self.exclusive_access

class ResourceHandler:
    @staticmethod
    def setResources(resources, rfm_test):
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