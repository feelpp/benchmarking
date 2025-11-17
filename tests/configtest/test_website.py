""" Tests for the feelpp.benchmarking.reframe.reporting module """
import tempfile,os,json
import pytest
from feelpp.benchmarking.reframe.reporting import WebsiteConfigCreator

@pytest.mark.parametrize(("config","empty_config"),[
    (WebsiteConfigCreator(basepath="./tests/data/non_exsistent_configs"), True),
    (WebsiteConfigCreator(basepath="./tests/data/configs"), False),
]
)
class TestWebisteConfig:
    """ Tests for the WebsiteConfigCreator class"""

    def test_init(self,config,empty_config):
        """Tests the class initialization
        Checks that config is loaded correctly if exists or initialized empty.
        """
        if empty_config:
            assert all(v == {} for v in config.config.values())
        else:
            with open("./tests/data/configs/website_config.json","r") as f:
                assert config.config == json.load(f)

    def test_updateExecutionMapping(self,config,empty_config):
        """ Tests for the updateExecutionMapping method."""
        config.updateExecutionMapping("test_app","test_mach","test_uc","test_itempath")

        assert "test_app" in config.config["execution_mapping"]
        assert "test_mach" in config.config["execution_mapping"]["test_app"]
        assert "test_uc" in config.config["execution_mapping"]["test_app"]["test_mach"]
        assert config.config["execution_mapping"]["test_app"]["test_mach"]["test_uc"] == {"platform":"local","path":"test_itempath"}

        #Test that existing info is replaced
        config.updateExecutionMapping("test_app","test_mach","test_uc","new_itempath")
        assert config.config["execution_mapping"]["test_app"]["test_mach"]["test_uc"]["path"] == "new_itempath"

    @pytest.mark.parametrize(("method","elt"),[
        (lambda c: c.updateUseCase,"use_cases"),
        (lambda c: c.updateMachine,"machines"),
        (lambda c: c.updateApplication,"applications"),
    ])
    def test_updates(self,config,empty_config,method,elt):
        """ Tests methods that update the config attribute"""
        new_element = "new_element"
        method(config)(new_element)
        assert new_element in config.config[elt]

    def test_save(self,config,empty_config):
        """Tests the save method"""
        with tempfile.NamedTemporaryFile() as temp:
            config.config_filepath = temp.name

            if empty_config:
                config.config = "TEST CONFIG FOR EMPTY"

            config.save()

            with open(temp.name,"r") as f:
                assert json.load(f) == config.config