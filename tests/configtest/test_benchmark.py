""" Tests for the configSchemas module """
import pytest
from feelpp.benchmarking.reframe.config.configSchemas import Sanity,CustomVariable,Scalability,Resources,Image,Platform,AdditionalFiles,ConfigFile
from pydantic import ValidationError



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
        plots= [],
        resources = Resources(tasks=1)
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
            json_report=plots,
            resources=resources
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
            parameters=[{"name":"param1","sequence":[]},{"name":"param2","sequence":[]}],
            plots=[{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"param2","label":"sec"}}]
        )

        with pytest.raises(ValidationError,match="Parameter not found"):
            self.initDefaultConfigFile(
                parameters=[{"name":"param1","sequence":[]},{"name":"param2","sequence":[]}],
                plots=[{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"unkownParam","label":"sec"}}]
            )

            self.initDefaultConfigFile(
                parameters=[{"name":"param1","sequence":[{"subparam1":"x","subparam2":"y"}]}],
                plots=[{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1.subparam1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"param1.subparam2","label":"sec"}}]
            )


        with pytest.raises(ValidationError,match="Parameter not found"):
            self.initDefaultConfigFile(
                parameters=[{"name":"param1","sequence":[{"subparam1":"x","subparam2":"y"}]}],
                plots=[{"title":"title","transformation":"performance","plot_types":["scatter"],"names":[],"xaxis":{"parameter":"param1.subparam1","label":"x"},"yaxis":{"label":"y"},"secondary_axis":{"parameter":"param1.unown","label":"sec"}}]
            )


    def test_checkAcceptedPlatforms(self):
        """Tests that the platform keys are correctly validated with only accepted platforms"""
        for plat in ["docker","apptainer","builtin"]:
            config_file = self.initDefaultConfigFile(platforms={plat:Platform()})
            assert plat in config_file.platforms

        with pytest.raises(ValueError,match="not implemented"):
            config_file = self.initDefaultConfigFile(platforms={"unkown":Platform()})
