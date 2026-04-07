import pytest
from feelpp.benchmarking.reframe.schemas.scalability import Stage
from pydantic import ValidationError

class TestScalability:
    #CustomVariable
    pass


class TestStage:
    def test_format(self):
        """ Tests the correct format and mandatory fields combinations"""
        with pytest.raises(ValidationError,match="variables_path must be specified if format == json"):
            stage = Stage(**{"name":"test_stage","filepath":"test_filepath","format":"json"})

        stage = Stage(**{"name":"test_stage","filepath":"test_filepath","format":"json","variables_path":"var1"})
        assert stage.variables_path == ["var1"]

        stage = Stage(**{"name":"test_stage","filepath":"test_filepath","format":"json","variables_path":["var2"]})
        assert stage.variables_path == ["var2"]

        with pytest.raises(ValidationError,match="variables_path cannot be specified with other format than json"):
            stage = Stage(**{"name":"test_stage","filepath":"test_filepath","format":"csv","variables_path":"test_varpath"})

        stage = Stage(**{"name":"test_stage","filepath":"test_filepath","format":"csv"})
        assert stage.variables_path == []

    def test_regex_validation(self):
        """ Tests mandatory regex fields and named/numbered groups """
        # Missing pattern
        with pytest.raises(ValidationError, match="regex must be specified if format == regex"):
            Stage(**{"name": "r_stage", "filepath": "file.txt", "format": "regex", "variable_value_group": "value"})

        # Missing variable_value_group
        with pytest.raises(ValidationError, match="variable_value_group must be specified if format == regex"):
            Stage(**{"name": "r_stage", "filepath": "file.txt", "format": "regex", "pattern": ".*"})

        # Valid named capture groups
        stage = Stage(
            name="r_stage",
            filepath="file.txt",
            format="regex",
            pattern="^(?P<name>[^:]+):\\s*(?P<value>[\\d.]+)$",
            variable_name_group="name",
            variable_value_group="value"
        )
        assert stage.format == "regex"
        assert stage.variable_name_group == "name"
        assert stage.variable_value_group == "value"


class TestAppOutput:
    pass
