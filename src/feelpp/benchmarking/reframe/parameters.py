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
        self.mode = param_config.mode
        self.active = param_config.active

    def parametrize(self):
        """ Pure Virtual function to parametrize a parameter"""
        raise NotImplementedError("This is a pure virtual method that should be overriden by inherited classes")


class LinspaceParameter(Parameter):
    def __init__(self, param_config):
        super().__init__(param_config)
        self.min = param_config.linspace.min
        self.max = param_config.linspace.max
        self.n_steps = param_config.linspace.n_steps

    def parametrize(self):
        yield from np.linspace(self.min,self.max,self.n_steps,endpoint=True,dtype=object)


class LogspaceParameter(Parameter):
    def __init__(self, param_config):
        super().__init__(param_config)
        self.min = param_config.linspace.min
        self.max = param_config.linspace.max
        self.n_steps = param_config.linspace.n_steps
        self.base = param_config.linspace.base

    def parametrize(self):
        yield from np.logspace(self.min,self.max,self.n_steps,endpoint=True,base=self.base,dtype=object)

class GeometricParameter(Parameter):
    def __init__(self, param_config):
        super().__init__(param_config)
        self.start = param_config.geometric.start
        self.ratio = param_config.geometric.ratio
        self.n_steps = param_config.geometric.n_steps

    def parametrize(self):
        yield from self.start * (self.ratio ** np.arange(self.n_steps,dtype=object))

class RangeParameter(Parameter):
    def __init__(self, param_config):
        super().__init__(param_config)
        self.min = param_config.range.min
        self.max = param_config.range.max
        self.step = param_config.range.step

    def parametrize(self):
        yield from np.arange(start=self.min, stop=self.max+self.step,step=self.step,dtype=object)

class SequenceParameter(Parameter):
    def __init__(self, param_config):
        super().__init__(param_config)
        self.sequence = param_config.sequence

    def parametrize(self):
        yield from self.sequence

class RepeatParameter(Parameter):
    def __init__(self, param_config):
        super().__init__(param_config)
        self.value = param_config.repeat.value
        self.count = param_config.repeat.count

    def parametrize(self):
        yield from [self.value]*self.count

class ZipParameter(Parameter):
    def __init__(self, param_config):
        super().__init__(param_config)
        self.parameter_generators = {
            subparam_config.name : ParameterFactory.create(subparam_config).parametrize()
            for subparam_config in param_config.zip
        }

    def parametrize(self):
        yield from ({key: value for key, value in zip(self.parameter_generators.keys(), values)} for values in zip(*self.parameter_generators.values()))

class ParameterFactory:
    """ Factory class to create Parameters for reframe tests"""
    @staticmethod
    def create(param_config):
        if param_config.mode == "linspace":
            return LinspaceParameter(param_config)
        elif param_config.mode == "range":
            return RangeParameter(param_config)
        elif param_config.mode == "logspace":
            return LogspaceParameter(param_config)
        elif param_config.mode == "sequence":
            return SequenceParameter(param_config)
        elif param_config.mode == "repeat":
            return RepeatParameter(param_config)
        elif param_config.mode == "geometric":
            return GeometricParameter(param_config)
        elif param_config.mode == "zip":
            return ZipParameter(param_config)
        else:
            raise ValueError(f"Unkown parameter type {param_config.range.mode}")
