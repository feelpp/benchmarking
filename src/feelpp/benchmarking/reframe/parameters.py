import reframe as rfm
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
    """ Parameter that generates evenly spaced samples using a min, max and a number of steps """
    def __init__(self, param_config):
        super().__init__(param_config)
        self.min = param_config.linspace.min
        self.max = param_config.linspace.max
        self.n_steps = param_config.linspace.n_steps

    def parametrize(self):
        yield from np.linspace(self.min,self.max,self.n_steps,endpoint=True,dtype=object)


class GeomspaceParameter(Parameter):
    """ Parameter that generates evenly spaced samples on a log scale using a min, max, a number of steps"""
    def __init__(self, param_config):
        super().__init__(param_config)
        self.min = param_config.geomspace.min
        self.max = param_config.geomspace.max
        self.n_steps = param_config.geomspace.n_steps

    def parametrize(self):
        yield from np.geomspace(self.min,self.max,self.n_steps,endpoint=True).astype(object)

class GeometricParameter(Parameter):
    """ Parameter that generates a geometric sequence a start, a ratio and a number of steps """
    def __init__(self, param_config):
        super().__init__(param_config)
        self.start = param_config.geometric.start
        self.ratio = param_config.geometric.ratio
        self.n_steps = param_config.geometric.n_steps

    def parametrize(self):
        yield from self.start * (self.ratio ** np.arange(self.n_steps,dtype=object))

class RangeParameter(Parameter):
    """ Parameter that generates an evenly spaced sequence from an interval and a step"""
    def __init__(self, param_config):
        super().__init__(param_config)
        self.min = param_config.range.min
        self.max = param_config.range.max
        self.step = param_config.range.step

    def parametrize(self):
        yield from np.arange(start=self.min, stop=self.max+self.step,step=self.step,dtype=object)

class SequenceParameter(Parameter):
    """ Parameter that creates a generator from a list"""
    def __init__(self, param_config):
        super().__init__(param_config)
        self.sequence = param_config.sequence

    def parametrize(self):
        yield from self.sequence

class RepeatParameter(Parameter):
    """ Parameter that creates a generator repeating a single value a number of times (the value can be of any type)"""
    def __init__(self, param_config):
        super().__init__(param_config)
        self.value = param_config.repeat.value
        self.count = param_config.repeat.count

    def parametrize(self):
        yield from [self.value]*self.count

class ZipParameter(Parameter):
    """ Parameter that creates a generator from its subparameters generators, zipped, in the form of [{"subparam1":value_1_1, ..., "subparamN":value_N_1}, ..., {"subparam1":value_1_M ,..., "subparamN":value_N_M}]."""
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
        elif param_config.mode == "geomspace":
            return GeomspaceParameter(param_config)
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



class ParameterHandler:
    def __init__(self,parameters_config):
        self.parameters_config = parameters_config
        self.parameters = {}
        self.nested_parameter_keys = {}

        for param_config in parameters_config:
            if not param_config.active:
                continue

            if param_config.mode=="zip":
                self.nested_parameter_keys[param_config.name] = [subparam.name for subparam in param_config.zip]
            elif param_config.mode=="sequence" and all(type(s)==dict and s.keys() for s in param_config.sequence):
                self.nested_parameter_keys[param_config.name] = list(param_config.sequence[0].keys())
            else:
                self.nested_parameter_keys[param_config.name] = []
            param_values = list(ParameterFactory.create(param_config).parametrize())
            self.parameters[param_config.name] = param_values

    def pruneParameterSpace(self,rfm_test):
        for param_config in self.parameters_config:
            if not param_config.conditions:
                continue

            active_parameter_value = str(getattr(rfm_test,param_config.name))
            filters_list = param_config.conditions.get(active_parameter_value)
            if not filters_list:
                continue

            active_filter_values = {}
            for filters in filters_list:
                for filter_name in filters.keys():
                    param_path = filter_name.split(".")
                    active_filter_values[filter_name] = getattr(rfm_test,param_path[0])
                    if len(param_path) > 1:
                        for p in param_path[1:]:
                            active_filter_values[filter_name] = active_filter_values[filter_name].get(p)

            is_valid = any(
                all(
                    active_filter_values[filter_key] in filter_values
                    for filter_key, filter_values in filters.items()
                )
                for filters in filters_list
            )

            rfm_test.skip_if(not is_valid , f"Invalid parameter combination ({active_filter_values}) for condition list {param_config.name}={active_parameter_value} condition list ({filters_list})", )

