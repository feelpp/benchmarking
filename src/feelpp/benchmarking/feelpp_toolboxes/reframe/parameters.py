import reframe.core.runtime as rt

class Parameter:
    def __init__(self,param_config):
        self.param_config = param_config

    def parametrize(self):
        pass


class NbTasks(Parameter):
    def __init__(self,param_config):
        super().__init__(param_config)

    def parametrize(self):
        for part in rt.runtime().system.partitions:
            nb_task = self.param_config.topology.min_cores_per_node
            yield nb_task
            while (nb_task < part.processor.num_cpus) and (nb_task < self.param_config.topology.max_cores_per_node):
                nb_task <<= 1
                yield nb_task

            if not (self.param_config.topology.min_nodes == 1 and self.param_config.topology.max_nodes == 1):
                if self.param_config.topology.max_nodes < part.devices[0].num_devices:
                    nb_nodes = self.param_config.topology.max_nodes
                else:
                    nb_nodes = part.devices[0].num_devices
                for i in range(self.param_config.topology.min_nodes+1, nb_nodes+1):
                    nb_task = i * part.processor.num_cpus
                    yield nb_task