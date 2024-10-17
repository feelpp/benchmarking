import reframe.core.runtime as rt
import numpy as np

class Parameter:
    """ Abstract calss for parameters """
    def __init__(self,param_config):
        """
        Args:
            param_config (Param). object from the pydantic schema representing a parameter
        """
        self.name = param_config.name
        self.active = param_config.active
        self.range = param_config.range

    def parametrize(self):
        """ Pure Virtual function to parametrize a parameter"""
        raise NotImplementedError("This is a pure virtual method that should be overriden by inherited classes")


class CoresParameter(Parameter):
    """ Parameter representing the number of tasks """
    def __init__(self,param_config):
        super().__init__(param_config)

    def parametrize(self):
        """Parametrize the number of tasks, depending on the desiring sequencing/configuration"""
        if self.range.generator == "double":
            for part in rt.runtime().system.partitions:
                nb_task = self.range.min_cores_per_node
                yield nb_task
                while (nb_task < part.processor.num_cpus) and (nb_task < self.range.max_cores_per_node):
                    nb_task <<= 1
                    yield nb_task

                if not (self.range.min_nodes == 1 and self.range.max_nodes == 1):
                    if self.range.max_nodes < part.devices[0].num_devices:
                        nb_nodes = self.range.max_nodes
                    else:
                        nb_nodes = part.devices[0].num_devices
                    for i in range(self.range.min_nodes+1, nb_nodes+1):
                        nb_task = i * part.processor.num_cpus
                        yield nb_task
        else:
            raise NotImplementedError

class StepParameter(Parameter):
    """ Parameter that changes following a step strategy """
    def __init__(self, param_config):
        super().__init__(param_config)

    def parametrize(self):
        if self.range.generator == "linear":
            assert self.range.n_steps is not None, "Number of steps must be specified for the linear generator"
            step = (self.range.max - self.range.min) / (self.range.n_steps - 1)
        elif self.range.generator == "constant":
            assert self.range.step is not None, "The step must be specified for the constant generator"
            step = self.range.step
        else:
            raise NotImplementedError

        current = self.range.min
        while current <= self.range.max:
            yield current
            current += step


class ListParameter(Parameter):
    """ Parameter that is given as a list """
    def __init__(self, param_config):
        super().__init__(param_config)

    def parametrize(self):
        if self.range.generator == "ordered":
            treated_list = self.range.sequence
        elif self.range.generator == "random":
            raise NotImplementedError
        else:
            raise NotImplementedError

        for current in treated_list:
            yield current



class ParameterFactory:
    """ Factory class to create Parameters for reframe tests"""
    @staticmethod
    def create(param_config):
        if param_config.range.mode == "cores":
            return CoresParameter(param_config)
        elif param_config.range.mode ==  "step":
            return StepParameter(param_config)
        elif param_config.range.mode ==  "list":
            return ListParameter(param_config)
        else:
            raise ValueError(f"Unkown parameter type {param_config.range.mode}")
