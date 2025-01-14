""" Tests related to machine configuration"""
import pytest
from feelpp.benchmarking.reframe.config.configMachines import Container, MachineConfig
from pydantic import ValidationError


class TestContainer:
    """ Tests for the Container pydantic schema """

    def test_optional(self):
        """ Tests that optional values are correctly initialized"""
        container = Container(**{"image_base_dir":"./tests/data/"})
        assert container.cachedir == None
        assert container.tmpdir == None
        assert container.options == []
        assert container.image_base_dir == "./tests/data/"

    def test_directoryCheck(self):
        """Tests the directory extistance verification.
        - Checks that no error is raised for existant dirs
        - Checks that no errir is raised for nonexistant dirs and dry_run true
        - Checks that errors are raised if directories do not exist and dry run flag is false"""
        Container(**{
            "image_base_dir":"./tests/data/",
            "cachedir":"./tests/data/",
            "tmpdir":"./tests/data/",
            "options":["--option1","--option2"]
        })

        Container.model_validate({
            "image_base_dir":"./nonexistent/",
            "cachedir":"./nonexistent/",
            "tmpdir":"./nonexistent/",
        },context={"dry_run":True})

        with pytest.raises(FileNotFoundError):
            Container.model_validate(
                { "image_base_dir":"./nonexistent/"},
                context={"dry_run":False}
            )
            Container.model_validate(
                { "image_base_dir":"./tests/data/", "cachedir":"./nonexistent/"},
                context={"dry_run":False}
            )
            Container.model_validate(
                { "image_base_dir":"./tests/data/", "tmpdir":"./nonexistent/"},
                context={"dry_run":False}
            )



class TestMachineValidation:
    """ Tests for the MachineConfig pydantic schema"""

    def test_defaults(self):
        """Tests that default values are correctly set for optional fields."""
        config = MachineConfig(
            machine="TestMachine",
            reframe_base_dir="path/to/reframe",
            reports_base_dir="path/to/reports",
            output_app_dir="path/to/output",
            targets="::"
        )

        assert config.active is True
        assert config.execution_policy == "serial"
        assert config.platform == "builtin"
        assert config.partitions == ["default"]
        assert config.prog_environments == ["default"]
        assert config.environment_map == {"default":["default"]}
        assert config.containers == {}

    def test_targetsValidation(self):
        """Tests validation of the `targets` field."""
        # Valid targets
        config = MachineConfig(
            machine="TestMachine",
            reframe_base_dir="path/to/reframe",
            reports_base_dir="path/to/reports",
            output_app_dir="path/to/output",
            targets="partition:apptainer:env"
        )
        assert config.targets == ["partition:apptainer:env"]
        assert config.platform == "apptainer"
        assert config.partitions == ["partition"]
        assert config.prog_environments == ["env"]
        assert config.environment_map == {"partition": ["env"]}

        # Invalid targets
        with pytest.raises(ValueError, match="Targets sould follow the syntax partition:plaform:environment"):
            MachineConfig(
                machine="TestMachine",
                reframe_base_dir="path/to/reframe",
                reports_base_dir="path/to/reports",
                output_app_dir="path/to/output",
                targets="invalid_target"
            )

        with pytest.raises(NotImplementedError, match="only specifying one platform is supported"):
            MachineConfig(
                machine="TestMachine",
                reframe_base_dir="path/to/reframe",
                reports_base_dir="path/to/reports",
                output_app_dir="path/to/output",
                targets=["partition1:apptainer:env1", "partition2:docker:env2"]
            )

    def test_partitionEnvsProd(self):
        """Tests cartesian product validation when `targets` is not specified."""
        config = MachineConfig(
            machine="TestMachine",
            reframe_base_dir="path/to/reframe",
            reports_base_dir="path/to/reports",
            output_app_dir="path/to/output",
            platform="apptainer",
            partitions=["partition1", "partition2"],
            prog_environments=["env1", "env2"]
        )
        assert config.targets is None
        assert config.platform == "apptainer"
        assert set(config.partitions) == {"partition1", "partition2"}
        assert set(config.prog_environments) == {"env1", "env2"}

        with pytest.raises(ValueError, match="Either specify the `targets` field or the .* fields for a cartesian product"):
            MachineConfig(
                machine="TestMachine",
                reframe_base_dir="path/to/reframe",
                reports_base_dir="path/to/reports",
                output_app_dir="path/to/output",
                platform="apptainer",
                partitions=[]
            )

    def test_checkContainerTypes(self):
        """Tests validation of `containers` field."""
        valid_containers = {
            "apptainer": Container(image_base_dir="tests/data"),
            "docker": Container(image_base_dir="tests/data")
        }

        config = MachineConfig(
            machine="TestMachine",
            reframe_base_dir="path/to/reframe",
            reports_base_dir="path/to/reports",
            output_app_dir="path/to/output",
            containers=valid_containers,
            targets=":apptainer:"
        )
        assert config.containers == valid_containers

        invalid_containers = {
            "unknown": Container(image_base_dir="tests/data")
        }

        with pytest.raises(ValidationError, match="unknown not implemented"):
            MachineConfig(
                machine="TestMachine",
                reframe_base_dir="path/to/reframe",
                reports_base_dir="path/to/reports",
                output_app_dir="path/to/output",
                containers=invalid_containers
            )