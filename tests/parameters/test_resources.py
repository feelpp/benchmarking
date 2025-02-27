import pytest
from feelpp.benchmarking.reframe.resources import TaskAndTaskPerNodeStrategy, NodesAndTasksPerNodeStrategy, TasksAndNodesStrategy, TasksStrategy, MemoryEnforcer, ExclusiveAccessEnforcer, ResourceHandler, GpusPerNodeStrategy


class ResourcesMocker:
    """ Mocks the resources object """
    def __init__(self, tasks = None, tasks_per_node = None, nodes = None, memory = None, exclusive_access = None, gpus_per_node = None):
        self.tasks = tasks
        self.tasks_per_node = tasks_per_node
        self.nodes = nodes
        self.memory = memory
        self.exclusive_access = exclusive_access
        self.gpus_per_node = gpus_per_node


class RfmTestMocker:
    """ Mocks the rfm_test object (a ReFrame Test) """
    def __init__(self, num_cpus, memory_per_node):
        self.current_partition = self.Partition(num_cpus=num_cpus, memory_per_node=memory_per_node)
        self.job = self.Job()

    class Job:
        def __init__(self):
            self.options = []
    class Partition:
        def __init__(self, num_cpus, memory_per_node):
            self.processor = self.Processor(num_cpus=num_cpus)
            self.extras = {"memory_per_node": memory_per_node}

        class Processor:
            def __init__(self, num_cpus):
                self.num_cpus = num_cpus


class TestResourcesStrategies:
    """ Tests the different strategies for setting resources """
    def strategyTest(self, strategy, resources, rfm_test, fails):
        """ Common test for all strategies
        Args:
            strategy (ResourceStrategy): The strategy to test
            resources (ResourcesMocker): The resources object
            rfm_test (RfmTestMocker): The rfm_test object
            fails (bool): Whether the test should fail or not
        """
        strategy.configure(resources, rfm_test)
        if fails:
            with pytest.raises(AssertionError):
                strategy.validate(rfm_test)
                return
        else:
            strategy.validate(rfm_test)


    @pytest.mark.parametrize(("tasks","expected_nodes"), [
        (128, 1), (256, 2), (64, 1), (32, 1), (280, 3), (384, 3),
        (0, False), (-1, False)
    ])
    def test_taskStrategy(self, tasks, expected_nodes):
        """ Tests the TaskStrategy
        Checks if the number of tasks and the number of tasks per node are set correctly
        Args:
            tasks (int): The number of tasks
            expected_nodes (int): The expected number of nodes
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)

        self.strategyTest(TasksStrategy(), ResourcesMocker(tasks=tasks), rfm_test, expected_nodes is False)
        if expected_nodes:
            assert rfm_test.num_tasks == tasks
            assert rfm_test.num_nodes == expected_nodes

    @pytest.mark.parametrize(("tasks","tasks_per_node","fails"), [
        (128, 128, False), (256, 128, False), (64, 64, False),
        (128, 256, True), (128, -1, True), (256,256,True), (200, 128, True)
    ])
    def test_tasksAndTasksPerNodeStrategy(self, tasks, tasks_per_node, fails):
        """ Tests the TaskAndTaskPerNodeStrategy
        Checks if the number of tasks and the number of tasks per node are set correctly
        Args:
            tasks (int): The number of tasks
            tasks_per_node (int): The number of tasks per node
            fails (bool): Whether the test should fail or not
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)

        self.strategyTest(TaskAndTaskPerNodeStrategy(), ResourcesMocker(tasks=tasks, tasks_per_node=tasks_per_node), rfm_test, fails)
        if not fails:
            assert rfm_test.num_tasks == tasks
            assert rfm_test.num_tasks_per_node == tasks_per_node

    @pytest.mark.parametrize(("tasks","nodes","expected_tasks_per_node","fails"), [
        (128, 1, 128, False), (256, 2, 128, False), (64, 1, 64, False),  (128, 3, 42, False),
        (128, 2, 64, False), (128, -1, 128, True), (256, 1 , 256, True)
    ])
    def test_tasksAndNodesStrategy(self, tasks, nodes, expected_tasks_per_node, fails):
        """ Tests the TasksAndNodesStrategy
        Checks if the number of tasks, the number of tasks per node and the number of nodes are set correctly
        Args:
            tasks (int): The number of tasks
            nodes (int): The number of nodes
            expected_tasks_per_node (int): The expected number of tasks per node
            fails (bool): Whether the test should fail or not
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)

        self.strategyTest(TasksAndNodesStrategy(), ResourcesMocker(tasks=tasks, nodes=nodes), rfm_test, fails)
        if not fails:
            assert rfm_test.num_tasks == tasks
            assert rfm_test.num_tasks_per_node == expected_tasks_per_node
            assert rfm_test.num_nodes == nodes

    @pytest.mark.parametrize(("tasks_per_node","nodes","expected_tasks","fails"), [
        (128, 1, 128, False), (128, 2, 256, False), (64, 1, 64, False), (128, 3, 384, False),
        (128, -1, 128, True), (256, 1, 256, True), (128, 3, 384, False)
    ])
    def test_nodesAndTasksPerNodeStrategy(self, tasks_per_node, nodes, expected_tasks, fails):
        """ Tests the NodesAndTasksPerNodeStrategy
        Checks if the number of tasks, the number of tasks per node and the number of nodes are set correctly
        Args:
            tasks_per_node (int): The number of tasks per node
            nodes (int): The number of nodes
            expected_tasks (int): The expected number of tasks
            fails (bool): Whether the test should fail or not
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)

        self.strategyTest(NodesAndTasksPerNodeStrategy(), ResourcesMocker(tasks_per_node=tasks_per_node, nodes=nodes), rfm_test, fails)
        if not fails:
            assert rfm_test.num_tasks_per_node == tasks_per_node
            assert rfm_test.num_nodes == nodes
            assert rfm_test.num_tasks == expected_tasks

    @pytest.mark.parametrize(("gpus_per_node","fails"),[
        (1,False), (22,False),
        (0, True), (-1, True)
    ])
    def test_GpusPerNodeStrategy(self,gpus_per_node,fails):
        """ Tests the GpusPerNodeStrategy
        Checks if the number of gpus_per_node is set
        Args:
            gpus_per_node (int): Number of gpus per node
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)
        rfm_test.num_tasks = 1
        self.strategyTest(GpusPerNodeStrategy(),ResourcesMocker(gpus_per_node=gpus_per_node),rfm_test, fails)
        if not fails:
            assert rfm_test.num_gpus_per_node == gpus_per_node

    @pytest.mark.parametrize(("tasks","memory","expected_nodes","expected_tasks_per_node"), [
        (128, 900, 1, 128), (128, 1000, 1, 128), (128, 1100, 2, 64), (128, 2100, 4, 42),
        (64, 500, 1, 64), (64, 1000, 1, 64), (64, 1100, 2, 32),
        (256, 900, 2, 128), (256, 1100, 2, 128), (256, 2500, 4, 85), (256, 3500, 4, 64),
        (301, 900, 3, 128), (301, 1100, 4, 100), (301, 4100, 6, 60)
    ])
    def test_memoryEnforcer(self, tasks, memory, expected_nodes, expected_tasks_per_node):
        """ Tests the MemoryEnforcer
        Checks if the number of nodes and the number of tasks per node are set correctly after enforcing the memory constraint
        Args:
            tasks (int): The number of tasks
            memory (int): The memory
            expected_nodes (int): The expected number of nodes
            expected_tasks_per_node (int): The expected number of tasks per node
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)
        TasksStrategy().configure(ResourcesMocker(tasks=tasks), rfm_test)

        memory_enforcer = MemoryEnforcer(memory)
        memory_enforcer.enforceMemory(rfm_test)

        assert rfm_test.num_nodes == expected_nodes
        assert rfm_test.num_tasks == tasks
        assert rfm_test.num_tasks_per_node == expected_tasks_per_node

    @pytest.mark.parametrize(("exclusive_access","expected"), [
        (True, True), (False, False), (None, True)
    ])
    def test_exclusiveAccessEnforcer(self, exclusive_access, expected):
        """ Tests the ExclusiveAccessEnforcer
        Checks if the exclusive access is set correctly
        Args:
            exclusive_access (bool): The exclusive access
            expected (bool): The expected exclusive access
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)
        exclusive_access_enforcer = ExclusiveAccessEnforcer(exclusive_access)
        exclusive_access_enforcer.enforceExclusiveAccess(rfm_test)

        assert rfm_test.exclusive_access == expected


class TestResourceHandler:
    """ Tests the ResourceHandler """
    def commonTest(self, resources):
        """ Common test for the ResourceHandler
        Checks if the resources are set correctly by verifying the attributes of the rfm_test object against the resources object
        Args:
            resources (ResourcesMocker): The resources object
        """
        rfm_test = RfmTestMocker(num_cpus=128, memory_per_node=1000)
        rfm_test = ResourceHandler().setResources(resources, rfm_test)
        for key in resources.__dict__.keys():
            if getattr(resources, key):
                if key == "exclusive_access":
                    assert getattr(rfm_test, key) == getattr(resources, key)
                elif key == "memory":
                    assert rfm_test.num_nodes
                else:
                    assert getattr(rfm_test, f"num_{key}") == getattr(resources, key)


    @pytest.mark.parametrize(("args", "fails"),[
        ({"tasks": 128, "tasks_per_node": 128, "exclusive_access":True}, False),
        ({"tasks": 128, "nodes": 1, "exclusive_access":True}, True),
        ({"tasks_per_node": 128, "nodes": 1, "exclusive_access":True} , False),
        ({"tasks": 128, "exclusive_access":False}, False),
        ({"tasks": 128, "memory":100,"exclusive_access":False}, False),
        ({"tasks":64,"gpus_per_node": 2, "memory":100,"exclusive_access":False}, False),
    ])
    def test_setResources(self, args, fails):
        """ Tests the ResourceHandler setResources method
        Checks if the resources are set correctly
        Args:
            args (dict): The arguments for the ResourcesMocker
            fails (bool): Whether the test should fail or not
        """
        resources = ResourcesMocker(**args)
        if fails:
            with pytest.raises(NotImplementedError):
                self.commonTest(resources)
        else:
            self.commonTest(resources)
