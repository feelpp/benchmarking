import pytest
import tempfile, os
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from feelpp.benchmarking.reframe.config.configReader import ConfigReader


class AdditionalFilesMocker:
    def __init__(self,description_filepath="",parameterized_descriptions_filepath=""):
        self.description_filepath=description_filepath
        self.parameterized_descriptions_filepath = parameterized_descriptions_filepath

class TestAdditionalFilesCopy:

    def test_copyFile(self):
        """Test the copyDescription method of the AppSetup class.
        It checks that a file is correctly copied as expected, with its content intact"""

        os.environ["MACHINE_CONFIG_FILEPATH"] = "./tests/data/configs/mockMachineConfig.json"
        os.environ["APP_CONFIG_FILEPATH"] = "./tests/data/configs/mockAppConfig.json"

        from feelpp.benchmarking.reframe.setup import AppSetup

        with tempfile.NamedTemporaryFile() as file:
            with open(file.name,"w") as f:
                f.write("TEST DESCRIPTION FILE")

            app_setup = AppSetup("./tests/data/configs/mockAppConfig.json",ConfigReader("./tests/data/configs/mockMachineConfig.json",MachineConfig).config)
            app_setup.reader.config.additional_files = True

            with tempfile.TemporaryDirectory() as tmp_dir:
                app_setup.copyFile(dir_path=tmp_dir,name="test_description",filepath=file.name)

                assert os.path.isfile(os.path.join(tmp_dir,"partials","test_description"))
                with open(os.path.join(tmp_dir,"partials","test_description"),"r") as f:
                    assert f.read() == "TEST DESCRIPTION FILE"