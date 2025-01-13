import pytest
import tempfile, os
from feelpp.benchmarking.reframe.outputs import OutputsHandler


class OutputsConfigMocker:
    def __init__(self,filepath="",format=""):
        self.filepath = filepath
        self.format = format

class AdditionalFilesMocker:
    def __init__(self,description_filepath="",parameterized_descriptions_filepath=""):
        self.description_filepath=description_filepath
        self.parameterized_descriptions_filepath = parameterized_descriptions_filepath

class TestOutputsHandler:

    @staticmethod
    def buildCsvString(columns,values):
        """Helper function to create the content of a CSV from a list of columns and a list of values"""
        assert len(columns) == len(values)
        return ",".join(columns) + "\n" + ",".join([str(v) for v in values])


    def test_getOutputsCsv(self):
        """Tests the getOutputs method with csv format"""
        file = tempfile.NamedTemporaryFile()
        columns = ["col1","col2","col3"]
        values = [1,2,3]
        with open(file.name,"w") as f:
            f.write(self.buildCsvString(columns,values))

        outputs_handler = OutputsHandler(
            [OutputsConfigMocker(filepath=file.name,format="csv")]
        )

        perfvars = outputs_handler.getOutputs()

        for i,column in enumerate(columns):
            assert perfvars[column].evaluate() == values[i]

        file.close()

    def test_copyDescription(self):
        """Test the copyDescription method of the OutputsHandler class.
        It checks that a file is correctly copied as expected, with its content intact"""
        with tempfile.NamedTemporaryFile() as file:
            with open(file.name,"w") as f:
                f.write("TEST DESCRIPTION FILE")

            outputs_handler = OutputsHandler(
                outputs_config = [],
                additional_files_config=AdditionalFilesMocker(description_filepath=file.name)
            )

            with tempfile.TemporaryDirectory() as tmp_dir:
                outputs_handler.copyDescription(dir_path=tmp_dir,name="test_description")

                assert os.path.isfile(os.path.join(tmp_dir,"partials","test_description"))
                with open(os.path.join(tmp_dir,"partials","test_description"),"r") as f:
                    assert f.read() == "TEST DESCRIPTION FILE"

    #TODO: This should be refactored when the OutputsHandler is reworked
    def test_copyParametrizedDescriptions(self):
        """Test the copyParametrizedDescriptions method of the OutputsHandler class.
        It checks that a file is correctly copied as expected, with its content intact"""
        with tempfile.NamedTemporaryFile() as file:
            with open(file.name,"w") as f:
                f.write("TEST PARAMETRIZED DESCRIPTION FILE")

            outputs_handler = OutputsHandler(
                outputs_config = [],
                additional_files_config=AdditionalFilesMocker(parameterized_descriptions_filepath=file.name)
            )

            with tempfile.TemporaryDirectory() as tmp_dir:
                outputs_handler.copyParametrizedDescriptions(dir_path=tmp_dir,name="test_parametrized_description")

                assert os.path.isfile(os.path.join(tmp_dir,"partials","test_parametrized_description"))
                with open(os.path.join(tmp_dir,"partials","test_parametrized_description"),"r") as f:
                    assert f.read() == "TEST PARAMETRIZED DESCRIPTION FILE"

