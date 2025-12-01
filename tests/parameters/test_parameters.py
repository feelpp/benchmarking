""" Tests for individual parameter generators"""



import numpy as np
import string
import pytest
from feelpp.benchmarking.reframe.parameters import ParameterFactory
from feelpp.benchmarking.reframe.schemas.parameters import Parameter

def createParameterDict(mode,param_config):
    """Helper function to create the expected dictionnary for the Parameter schema, with the default name of "test_param"
    Args:
        mode (str): The parameter mode
        param_config (dict|list): The parameter generator configuration. IT is what goes under the parameter mode, for example, {"min":0,"max":1,"n_steps":5} for the linspace parameter.
    returns
        dict: expected dictinonary to initialize the parameter object (schame valid)
    """
    return { "name": "test_param", "mode": mode, mode: param_config }

def genericParameterTest(mode,param_config,expected=None):
    """Helper function to compare the result of any parameter .parametrize() method agains an expected value.
    If no expected value is provided, it will be calculated here depending on the parameter mode.
    Args:
        mode (str): The parameter mode
        param_config (dict|list): The parameter generator configuration. IT is what goes under the parameter mode, for example, {"min":0,"max":1,"n_steps":5} for the linspace parameter.
        expected: The expected result of the .parametrize() method of the parameter object.
    Raises:
        AssertionError: if the result does not match the expected value.
    """
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
        elif mode == "zip":
            pass
        else:
            raise ValueError(f"Random Tests for mode {mode} not implemented...")

    if mode in ["repeat","sequence"]:
        assert np.array_equal(result, expected), f"Expected result does not match for {mode}"
        return

    if mode == "zip":
        assert result == expected
        return

    assert np.allclose(result, expected, atol=1e-12), f"Expected result does not match for {mode}"


def parameter_test_cases():
    """ Returns all parameter cases to test. Contains the mode, the parameter configuration and the expected values"""
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
            {"param_config": {"start": 5, "ratio": -1, "n_steps": 5}, "expected": [5, -5, 5, -5, 5]},  # Negative ratio
            {"param_config": {"start": 0, "ratio": 2, "n_steps": 4}, "expected": [0, 0, 0, 0]},  # Zero start
            {"param_config": {"start": 1, "ratio": 0, "n_steps": 4}, "expected": [1, 0, 0, 0]},  # Zero ratio
            {"param_config":{"start": np.random.uniform(-100,100), "ratio": np.random.uniform(-100,100), "n_steps": np.random.randint(1,100)}, "expected":None},  # Random
        ],
        "range":[
            {"param_config": {"min": 0, "max": 10, "step": 2}, "expected": [0, 2, 4, 6, 8, 10]},  # Simple range
            {"param_config": {"min": -10, "max": 10, "step": 5}, "expected": [-10, -5, 0, 5, 10]},  # Negative step
            {"param_config": {"min": 0, "max": 10, "step": 0.5}, "expected": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]},  # Float step
            {"param_config": {"min": 10, "max": 0, "step": -2}, "expected": [10, 8, 6, 4, 2, 0]},  # Decreasing range
            {"param_config":{"min": np.random.uniform(0,50), "max": np.random.uniform(51,100), "step": np.random.uniform(1,100)}, "expected":None},  #Random
            {"param_config":{"min": np.random.uniform(50,100), "max": np.random.uniform(0,50), "step": np.random.uniform(-100,-1)}, "expected":None},  #Random
        ],
        "sequence":[
            {"param_config":np.random.uniform(-100,100,100).tolist(), "expected":None},  #Random
            {"param_config": [1, 2, 3, 4, 5], "expected": [1, 2, 3, 4, 5]},  # Simple sequence
            {"param_config": ["a", "b", "c"], "expected": ["a", "b", "c"]},  # String sequence
            {"param_config": [np.random.choice(list(string.ascii_letters)) for _ in range(10)], "expected": None},  # Random letter sequence
        ],
        "repeat":[
            {"param_config":{"value":np.random.randint(100),"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":np.random.uniform(-100,100),"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":np.random.choice(list(string.ascii_letters)),"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":[np.random.choice(list(string.ascii_letters))],"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config":{"value":{np.random.choice(list(string.ascii_letters)):np.random.choice(list(string.ascii_letters))},"count":np.random.randint(100)},"expected":None},  #Random
            {"param_config": {"value": "test_value", "count": 5}, "expected": ["test_value"] * 5},  # Repeat a string
            {"param_config": {"value": [1, 2], "count": 3}, "expected": [[1, 2]] * 3},  # Repeat a list
        ],
        "zip":[
            # Basic test: zip two parameters
            {
                "param_config": [
                    {"name": "param1", "mode": "range", "range": {"min": 0, "max": 10, "step": 5}},
                    {"name": "param2", "mode": "linspace", "linspace": {"min": 0, "max": 5, "n_steps": 3}}
                ],
                "expected": [ {"param1": 0, "param2": 0.0}, {"param1": 5, "param2": 2.5}, {"param1": 10, "param2": 5.0} ]
            },
            # Test with complex subparameters
            {
                "param_config": [
                    {"name": "param1", "mode": "geomspace", "geomspace": {"min": 1, "max": 100, "n_steps": 3}},
                    {"name": "param2", "mode": "geometric", "geometric": {"start": 1, "ratio": 2, "n_steps": 3}}
                ],
                "expected": [ {"param1": 1.0, "param2": 1}, {"param1": 10.0, "param2": 2}, {"param1": 100.0, "param2": 4} ]
            },
            # Edge case: empty sequences
            {
                "param_config": [
                    {"name": "param1", "mode": "sequence", "sequence": []},
                    {"name": "param2", "mode": "sequence", "sequence": []}
                ],
                "expected": []
            },
            #Nested zips
            {
                "param_config": [
                    {
                        "name": "param1",
                        "mode": "zip",
                        "zip": [
                            {"name": "param2", "mode": "linspace", "linspace": {"min": 0, "max": 10, "n_steps": 3}},
                            {"name": "param3", "mode": "range", "range": {"min": 1, "max": 5, "step": 2}}
                        ]
                    },
                    {
                        "name": "param4",
                        "mode": "zip",
                        "zip": [
                            {"name": "param5", "mode": "repeat", "repeat": {"value": 10, "count": 3}},
                            {"name": "param6", "mode": "sequence", "sequence": [1, 2, 3]}
                        ]
                    }
                ],
                "expected": [
                    {"param1": {"param2": 0.0, "param3": 1}, "param4": {"param5": 10, "param6": 1}},
                    {"param1": {"param2": 5.0, "param3": 3}, "param4": {"param5": 10, "param6": 2}},
                    {"param1": {"param2": 10.0, "param3": 5}, "param4": {"param5": 10, "param6": 3}}
                ]
            },
            #Zipping 4 parameters
            {
                "param_config": [
                    {"name": "param1", "mode": "linspace", "linspace": {"min": 1, "max": 5, "n_steps": 3}},
                    {"name": "param2", "mode": "geomspace", "geomspace": {"min": 1, "max": 100, "n_steps": 3}},
                    {"name": "param3", "mode": "repeat", "repeat": {"value": 2, "count": 3}},
                    {"name": "param4", "mode": "range", "range": {"min": 0, "max": 6, "step": 2}}
                ],
                "expected": [
                    {"param1": 1.0, "param2": 1.0, "param3": 2, "param4": 0},
                    {"param1": 3.0, "param2": 10.0, "param3": 2, "param4": 2},
                    {"param1": 5.0, "param2": 100.0, "param3": 2, "param4": 4}
                ]
            }
        ]
    }


@pytest.mark.parametrize("mode, param_config, expected", [
    (mode, test_case["param_config"], test_case["expected"])
    for mode, cases in parameter_test_cases().items()
    for test_case in cases
])
def test_parameterParametrization(mode, param_config, expected):
    """Test parameterization for different modes. Given by the `parameter_test_cases()` function"""
    genericParameterTest(mode, param_config, expected)