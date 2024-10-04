import reframe.core.runtime as rt
import numpy as np

class Parameter:
    """ Abstract calss for parameters """
    def __init__(self,param_config):
        """
        Args:
            param_config (Param). object from the pydantic schema representing a parameter
        """
        self.param_config = param_config

    def parametrize(self):
        """ Pure Virtual function to parametrize a parameter"""
        raise NotImplementedError("This is a pure virtual method that should be overriden by inherited classes")


class NbTasks(Parameter):
    """ Parameter representing the number of tasks """
    def __init__(self,param_config):
        super().__init__(param_config)

    def parametrize(self):
        """Parametrize the number of tasks, depending on the desiring sequencing/configuration"""
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

class Discretization(Parameter):
    """ Parameter representing the discretization of the input data (mesh size, different meshes) """
    def __init__(self, param_config):
        super().__init__(param_config)

    def parametrize(self):
        if self.param_config.type == "continuous":
            match self.param_config.sequencing.generator:
                case "default" | "n_steps":
                    step = (self.param_config.hsize_range.max - self.param_config.hsize_range.min) / (self.param_config.sequencing.n_steps - 1)
                case "step":
                    step = self.param_config.sequencing.step
                case _:
                    raise NotImplementedError

            for current_h in np.arange( self.param_config.hsize_range.min,  self.param_config.hsize_range.max+step, step):
                if current_h <= self.param_config.hsize_range.max:
                    yield current_h

        elif self.param_config.type == "discrete":
            pass
        else:
            raise ValueError("[ THIS ERROR SHOULD NEVER BE SEEN ] Param type must be continuous or discrete.")