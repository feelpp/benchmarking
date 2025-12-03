import tempfile, math, pytest
from feelpp.benchmarking.json_report.schemas.dataRefs import Preprocessor, DataField

class TestPreprocessor:

    # ------------------------------------------------------------------
    # Preprocessor: parsing
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("inputVal,expectedModule,expectedFunction",
        [
            ("math:ceil", "math", "ceil"),
            ({"module":"math","function":"ceil"}, "math", "ceil")
        ]
    )
    def test_preprocessorParseStringOrDict(self, inputVal, expectedModule, expectedFunction):
        prep = Preprocessor.model_validate(inputVal)
        assert prep.module.__name__ == expectedModule
        assert prep.function is getattr(math, expectedFunction)
        assert prep.function(1.5) == 2

    def test_preprocessorInvalidStringRaises(self):
        with pytest.raises(ValueError):
            Preprocessor.model_validate("invalidstring")

    # ------------------------------------------------------------------
    # Preprocessor apply
    # ------------------------------------------------------------------
    def test_preprocessorApplyCallsFunction(self, tmp_path):
        # create dummy module dynamically
        module_path = tmp_path / "dummy_module.py"
        module_path.write_text("def double(x): return x*2")
        prep = Preprocessor(module = str(module_path), function="double")
        assert prep.apply(3) == 6


class TestDataField:
    # ------------------------------------------------------------------
    # DataFile: coerceExpose
    # ------------------------------------------------------------------
    def test_dataFileCoerceExposeSetsName(self):
        with tempfile.NamedTemporaryFile(suffix=".csv") as tmp:
            df = DataField.model_validate({"name":"data1", "filepath":tmp.name, "expose":True}, context={"report_filepath":tmp.name})
            assert df.expose == "data1"

    def test_dataFileCoerceExposeKeepsString(self):
        with tempfile.NamedTemporaryFile(suffix=".csv") as tmp:
            df = DataField.model_validate({"name":"data1", "filepath":tmp.name, "expose":"custom"},context={"report_filepath":tmp.name})
            assert df.expose == "custom"

    # ------------------------------------------------------------------
    # DataFile: infer format
    # ------------------------------------------------------------------
    def test_dataFileInferFormatFromFilepath(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            df = DataField.model_validate({"name":"data1", "filepath":tmp.name, "format":"json", "expose":"custom"},context={"report_filepath":tmp.name})
            assert df.format == "json"