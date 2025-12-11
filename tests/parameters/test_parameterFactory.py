""" Tests the parameterFactory class"""

import pytest
from feelpp.benchmarking.reframe.parameters import ParameterFactory, LinspaceParameter, RangeParameter, GeomspaceParameter, SequenceParameter, RepeatParameter, GeometricParameter, ZipParameter
from feelpp.benchmarking.reframe.schemas.parameters import Parameter



@pytest.mark.parametrize("param_config, expected_type", [
    ({"name":"linspace_param", "linspace": {"min": 0, "max": 10, "n_steps": 5}}, LinspaceParameter),
    ({"name":"range_param", "range": {"min": 0, "max": 10, "step": 2}}, RangeParameter),
    ({"name":"geomspace_param", "geomspace": {"min": 1, "max": 3, "n_steps": 3}}, GeomspaceParameter),
    ({"name":"sequence_param", "sequence": [1, 2, 3]}, SequenceParameter),
    ({"name":"repeat_param", "repeat": {"value": 5, "count": 3}}, RepeatParameter),
    ({"name":"geometric_param", "geometric": {"start": 1, "ratio": 2, "n_steps": 4}}, GeometricParameter),
    ({"name":"zip_param", "zip": [
        {"name":"range_param", "range": {"min": 0, "max": 10, "step": 1}},
        {"name":"sequence_param", "sequence": [1, 2, 3]}
    ]}, ZipParameter)
])
def test_parameterFactory(param_config, expected_type):
    """Checks the correct instantiation of parameters from the ParameterFactory
    Also checks that all parameters are equiped with a `parametrize` method.
    Args:
        param_config dict: The dictionary fed to the parameter object to instantiate it.
        expected_type: The class (type) that the parameterFactory should return for the given parameter mode (linspace, range, ...)
    """
    param = ParameterFactory.create(Parameter(**param_config))
    assert param.parametrize()
    assert isinstance(param, expected_type)

