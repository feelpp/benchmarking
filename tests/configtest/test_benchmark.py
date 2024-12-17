""" Tests for the configSchemas module """
import pytest
from feelpp.benchmarking.reframe.config.configSchemas import Sanity,CustomVariable,Scalability,Image,Platform,AdditionalFiles,ConfigFile
from feelpp.benchmarking.reframe.config.configParameters import Parameter
from feelpp.benchmarking.reframe.config.configPlots import Plot
from pydantic import ValidationError



class TestImage:
    """Tests for the Image schema"""

    dummy_image_path = "tests/data/configs/mockAppConfig.json"

    def test_extractProtocol(self):
        """Tests the correct extraction of the protocol from the image name"""
        image = Image(name=self.dummy_image_path)
        assert image.protocol == "local"
        assert image.name == self.dummy_image_path

        with pytest.raises(ValueError,match="Unkown Protocol"):
            image = Image(name="unkown_local://tests/data/configs")

        image = Image(name="docker://test_name")
        assert image.protocol == "docker"
        assert image.name == "docker://test_name"


    def test_checkImage(self):
        """Tests that checking if image exists is done correctly"""

        with pytest.raises(FileNotFoundError):
            image = Image(name="nonexistant_image.sif")

        #Dry run
        image = Image.model_validate({"name":"nonexistant_image.sif"},context={"dry_run":True})
        assert image.protocol == "local"


class TestPlatform:
    pass

class TestAdditionalFiles:
    pass

class TestConfigFile:
    """Tests for the ConfigFile Schema"""

    def initDefaultConfigFile(
        self,
        executable ="x",
        timeout="1-0:0:0",
        use_case_name="uc",
        options=[],outputs=[],
        scalability=Scalability(directory="",stages=[]),
        sanity=Sanity(error=[],success=[]),
        parameters=[],
        platforms = {},
        plots= []
    ):
        return ConfigFile(
            executable=executable,
            timeout=timeout,
            use_case_name=use_case_name,
            options=options,
            outputs=outputs,
            scalability=scalability,
            sanity=sanity,
            parameters=parameters,
            platforms=platforms,
            plots=plots
        )

    @pytest.mark.parametrize(("timeout","raises"),[
        ("1-0:0:0",False), ("0-12:30:45",False), ("23-23:0:59",False),
        ("1:00:00",True), ("01-100:00:00",True), ("1-25:00:00",True),
        ("1-00:60:00",True), ("1-00:00:60",True),
        ("not-a-timeout",True), ("1-12:30",True),
    ])
    def test_validateTimeout(self,timeout,raises):
        """ Tests that the timeout format is correctly validated """
        if raises:
            with pytest.raises(ValidationError):
                config_file = self.initDefaultConfigFile(timeout=timeout)
        else:
            config_file = self.initDefaultConfigFile(timeout=timeout)
            assert config_file.timeout == timeout


    def test_plotAxisValidation(self):
        """ Tests that plot axis parameters matches actual config parameters"""
        self.initDefaultConfigFile(
            parameters=[Parameter(**{"name":"param1","sequence":[]}),Parameter(**{"name":"param2","sequence":[]})],
            plots=[Plot(**{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"param2","label":"sec"}})]
        )

        with pytest.raises(ValidationError,match="Parameter not found"):
            self.initDefaultConfigFile(
                parameters=[Parameter(**{"name":"param1","sequence":[]}),Parameter(**{"name":"param2","sequence":[]})],
                plots=[Plot(**{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"unkownParam","label":"sec"}})]
            )

            self.initDefaultConfigFile(
                parameters=[Parameter(**{"name":"param1","sequence":[{"subparam1":"x","subparam2":"y"}]})],
                plots=[Plot(**{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1.subparam1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"param1.subparam2","label":"sec"}})]
            )


        with pytest.raises(ValidationError,match="Parameter not found"):
            self.initDefaultConfigFile(
                parameters=[Parameter(**{"name":"param1","sequence":[{"subparam1":"x","subparam2":"y"}]})],
                plots=[Plot(**{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1.subparam1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"param1.unown","label":"sec"}})]
            )


    def test_checkAcceptedPlatforms(self):
        """Tests that the platform keys are correctly validated with only accepted platforms"""
        for plat in ["docker","apptainer","builtin"]:
            config_file = self.initDefaultConfigFile(platforms={plat:Platform()})
            assert plat in config_file.platforms

        with pytest.raises(ValueError,match="not implemented"):
            config_file = self.initDefaultConfigFile(platforms={"unkown":Platform()})