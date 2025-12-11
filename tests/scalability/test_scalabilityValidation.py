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

class TestAppOutput:
    pass
