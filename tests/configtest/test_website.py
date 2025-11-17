""" Tests for the feelpp.benchmarking.reframe.reporting module """
import tempfile, os, json
import pytest
from feelpp.benchmarking.reframe.reporting import WebsiteConfigCreator

@pytest.mark.parametrize(("config","empty_config"),[
    (WebsiteConfigCreator(basepath="./tests/data/non_existent_configs"), True),
    (WebsiteConfigCreator(basepath="./tests/data/configs"), False),
])
class TestWebsiteConfig:
    """ Tests for the WebsiteConfigCreator class"""

    def test_init(self, config, empty_config):
        """Tests the class initialization"""
        if empty_config:
            # Check that essential keys exist in the empty config
            assert "components" in config.config
            assert "machines" in config.config["components"]
            assert "applications" in config.config["components"]
            assert "use_cases" in config.config["components"]
        else:
            with open("./tests/data/configs/website_config.json", "r") as f:
                assert config.config == json.load(f)

    def test_updateExecutionMapping(self, config, empty_config):
        """ Tests the updateExecutionMapping method """
        config.updateExecutionMapping("test_app", "test_mach", "test_uc", "test_itempath")

        mapping = config.config["component_map"]["mapping"]

        assert "test_mach" in mapping
        assert "test_app" in mapping["test_mach"]
        assert "test_uc" in mapping["test_mach"]["test_app"]
        assert mapping["test_mach"]["test_app"]["test_uc"]["path"] == "test_itempath"
        assert mapping["test_mach"]["test_app"]["test_uc"]["platform"] == "local"

        # Test that existing info is replaced
        config.updateExecutionMapping("test_app", "test_mach", "test_uc", "new_itempath")
        assert mapping["test_mach"]["test_app"]["test_uc"]["path"] == "new_itempath"

    @pytest.mark.parametrize(("method","elt"),[
        (lambda c: c.updateUseCase, "use_cases"),
        (lambda c: c.updateMachine, "machines"),
        (lambda c: c.updateApplication, "applications"),
    ])
    def test_updates(self, config, empty_config, method, elt):
        """ Tests methods that update the components """
        new_element = "new_element"
        method(config)(new_element)
        assert new_element in config.config["components"][elt]

    def test_save(self, config, empty_config):
        """Tests the save method"""
        with tempfile.NamedTemporaryFile("w+", delete=True) as temp:
            config.config_filepath = temp.name

            if empty_config:
                config.config = {"test": "CONFIG_FOR_EMPTY"}

            config.save()

            with open(temp.name, "r") as f:
                assert json.load(f) == config.config