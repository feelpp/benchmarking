import pytest, os
import reframe as rfm
from feelpp.benchmarking.reframe.parameters import ParameterFactory
from unittest.mock import patch, MagicMock


def configure_mock_runtime(mock_runtime):
    mock_partition = MagicMock()
    mock_partition.name = 'mock_partition'
    mock_partition.processor.num_cpus = 4

    mock_environ = MagicMock()
    mock_environ.name = 'mock_env'

    mock_runtime().system = MagicMock()
    mock_runtime().system.partitions = [mock_partition]
    mock_runtime().system.environs = [mock_environ]

    return mock_partition, mock_environ
@pytest.fixture(autouse=True)
def setup_environment():
    """Set environment variables required for ReFrame tests."""
    os.environ["MACHINE_CONFIG_FILEPATH"] = "./config/machines/gaya_ci.json"
    os.environ["APP_CONFIG_FILEPATH"] = "./tests/data/parameters/mockAppConfig.json"


class TestReframeParameters:
    """Tests parameter manipulation inside the ReFrame pipeline
    It initializes the ReFrame Setup with dummy configurations.
    """

    @patch('reframe.core.runtime.runtime')
    def test_parametersInit(self, mock_runtime):
        """ Checks that the `parameters` attribute is correctly constructed
        Checks that all reframe parameter are initialized as attributes
        """
        configure_mock_runtime(mock_runtime)
        from feelpp.benchmarking.reframe.setup import ReframeSetup

        rfm_setup = ReframeSetup
        input_parameters = rfm_setup.app_setup.reader.config.parameters
        subparameter_map = rfm_setup.parameters

        for parameter in input_parameters:
            assert parameter.name in subparameter_map
            if parameter.mode == "zip":
                assert subparameter_map[parameter.name] == [subp.name for subp in parameter.zip]
            elif parameter.mode == "sequence" and all(type(s)==dict and s.keys() for s in parameter.sequence):
                print(parameter.sequence)
                assert all(subp in subparameter_map[parameter.name] for subp in parameter.sequence[0].keys())
            else:
                assert subparameter_map[parameter.name] == []
            assert hasattr(rfm_setup, parameter.name)

    @patch('reframe.core.runtime.runtime')
    def test_parameterValues(self, mock_runtime):
        """Verify parameter values are correctly initialized in ReFrame."""
        configure_mock_runtime(mock_runtime)
        from feelpp.benchmarking.reframe.setup import ReframeSetup

        rfm_setup = ReframeSetup()
        input_parameters = rfm_setup.app_setup.reader.config.parameters

        for param_name, rfm_param in rfm_setup._rfm_param_space.params.items():
            param_values = list(
                ParameterFactory.create(next(p for p in input_parameters if p.name == param_name)).parametrize()
            )
            assert tuple(param_values) == rfm_param.values

    @patch('reframe.core.runtime.runtime')
    def test_setupParameters(self, mock_runtime):
        pass