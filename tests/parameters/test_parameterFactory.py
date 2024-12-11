import pytest
from feelpp.benchmarking.reframe.parameters import ParameterFactory, LinspaceParameter, RangeParameter, GeomspaceParameter, SequenceParameter, RepeatParameter, GeometricParameter, ZipParameter
from feelpp.benchmarking.reframe.config.configParameters import Parameter
import numpy as np
import string



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
    """
    param = ParameterFactory.create(Parameter(**param_config))
    assert param.parametrize()
    assert isinstance(param, expected_type)


def createParameterDict(mode,param_config):
    return { "name": "test_param", "mode": mode, mode: param_config }

def genericParameterTest(mode,param_config,expected):
    param = ParameterFactory.create(Parameter(**createParameterDict(mode,param_config)))
    result = list(param.parametrize())
    if not expected:
        if mode == "linspace":
            expected = np.linspace(param_config["min"],param_config["max"],param_config["n_steps"],endpoint=True)
        elif mode == "geomspace":
            expected = np.geomspace(param_config["min"],param_config["max"],param_config["n_steps"],endpoint=True)
        elif mode == "geometric":
            expected = param_config["start"] * (param_config["ratio"] ** np.arange(param_config["n_steps"]))
        elif mode == "range":
            expected = np.arange(start=param_config["min"], stop=param_config["max"]+param_config["step"],step=param_config["step"])
        elif mode == "sequence":
            expected = param_config
        elif mode == "repeat":
            expected = [param_config["value"]]*param_config["count"]
            assert np.array_equal(result, expected)
            return
        elif mode == "zip":
            pass
        else:
            raise ValueError(f"Random Tests for mode {mode} not implemented...")

    assert np.allclose(result, expected, atol=1e-12), f"Expected result does not match for {mode}"


def parameter_test_cases():
    return {
        "linspace":[
            {"param_config":{"min": 0, "max": 10, "n_steps": 5}, "expected":[0.0, 2.5, 5.0, 7.5, 10.0]},  # Basic example
            {"param_config":{"min": -5, "max": 5, "n_steps": 6}, "expected":[-5.0, -3.0, -1.0, 1.0, 3.0, 5.0]},  # oposed min-max
            {"param_config":{"min": -5, "max": 0, "n_steps": 6}, "expected":[-5.0, -4.0, -3.0, -2.0, -1.0, -0.0]},  # negative
            {"param_config":{"min": 10, "max": 0, "n_steps": 5}, "expected":[10.0, 7.5, 5.0, 2.5,0.0]},  # Decreasing
            {"param_config":{"min": 0.0, "max": 0.01, "n_steps": 100}, "expected":np.linspace(0.0, 0.01, 100).tolist()},  # Many steps
            {"param_config":{"min": 0.1, "max": 0.9, "n_steps": 5}, "expected":[0.1, 0.3, 0.5, 0.7, 0.9]},  # Uniform distribution
            {"param_config":{"min": 0, "max": 1000, "n_steps": 1}, "expected":[0.0]},  # Single step (edge case)
            {"param_config":{"min": np.random.uniform(-100,100), "max": np.random.uniform(-100,100), "n_steps": np.random.randint(2,100)}, "expected":None} #Random
        ],
        "geomspace":[
            {"param_config":{"min": 1, "max": 1000, "n_steps": 4}, "expected":[1, 10, 100, 1000]},  # Simple geometric space
            {"param_config":{"min": 1, "max": 16, "n_steps": 5}, "expected":[1.0, 2.0, 4.0, 8.0, 16.0]},  # Geometric with powers of 2
            {"param_config":{"min": 1000, "max": 1, "n_steps": 4}, "expected":[1000.0, 100.0, 10.0, 1.0]},  # Decreasing
            {"param_config":{"min": 0.5, "max": 10.75, "n_steps": 6}, "expected":[0.5, 0.92354422, 1.70586787, 3.15088883, 5.81997035, 10.75]},  # float values
            {"param_config":{"min": -1000, "max": -1, "n_steps": 4}, "expected":[-1000.0, -100.0, -10.0, -1.0]}, #Negative
            {"param_config":{"min": np.random.uniform(0,100), "max": np.random.uniform(0,100), "n_steps": np.random.randint(2,100)}, "expected":None} #Random
        ],
        "geometric":[
            {"param_config":{"start": 1, "ratio": 2, "n_steps": 4}, "expected":[1, 2, 4, 8]},  # Simple geometric space
            {"param_config":{"start": np.random.uniform(-100,100), "ratio": np.random.uniform(-100,100), "n_steps": np.random.randint(1,100)}, "expected":None},  # Random
        ],
        "range":[
            {"param_config":{"min": np.random.uniform(-100,100), "max": np.random.uniform(-100,100), "step": np.random.uniform(-100,100)}, "expected":None},  #Random
        ],
        "sequence":[
            {"param_config":np.random.uniform(-100,100,100).tolist(), "expected":None},  #Random
        ],
        "repeat":[
            {"param_config":{"value":np.random.randint(100),"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":np.random.uniform(-100,100),"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":np.random.choice(list(string.ascii_letters)),"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":[np.random.choice(list(string.ascii_letters))],"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":{np.random.choice(list(string.ascii_letters)):np.random.choice(list(string.ascii_letters))},"count":np.random.randint(100)},"expected":None}  #Random

        ],
        "zip":[]
}


@pytest.mark.parametrize("mode, param_config, expected", [
    (mode, test_case["param_config"], test_case["expected"])
    for mode, cases in parameter_test_cases().items()
    for test_case in cases
])
def test_parameter_parametrization(mode, param_config, expected):
    """Test parameterization for different modes."""
    genericParameterTest(mode, param_config, expected)