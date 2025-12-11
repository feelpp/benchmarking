import tempfile, math, pytest, warnings
from feelpp.benchmarking.json_report.schemas.dataRefs import *

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
    @pytest.mark.parametrize( "suffix,fmt,exp_data_type", [
        (".csv", "csv", "DataTable"), (".json", "json", "Object"), (".raw", "raw","Raw"),(".unkown","raw","Raw")
    ])
    def test_inferSource_file(self, suffix, fmt, exp_data_type):
        with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                df = DataField.model_validate(
                    {"name": "data1", "filepath": tmp.name},
                    context={"report_filepath": tmp.name},
                )
            assert isinstance(df.source, DataFile)
            assert df.source.filepath == tmp.name
            assert df.source.format == fmt
            assert df.type == exp_data_type

    @pytest.mark.parametrize(
        "data_type, extra, expected_class, expected_attr, expected_value",
        [
            ("DataTable", {"columns": [{"name":"a","values":["a1"]}, {"name":"b","values":["b1"]}]}, InlineTable, "columns", [InlineTableColumn(name="a",values=["a1"]), InlineTableColumn(name="b",values=["b1"])]),
            ("Object", {"object": {"k": 1}}, InlineObject, "object", {"k": 1}),
            ("Raw", {"value": "test"}, InlineRaw, "value", "test"),
        ],
    )
    def test_inferSource_inline(self,data_type, extra, expected_class, expected_attr, expected_value):
        df = DataField.model_validate({"name": "x", "type": data_type, **extra})

        assert isinstance(df.source, expected_class)
        assert getattr(df.source, expected_attr) == expected_value



class TestTableOptions:

    # ------------------------------------------------------------------
    # Defaults / empty initialization
    # ------------------------------------------------------------------
    def test_emptyTableDefaults(self):
        t = TableOptions()
        assert t.computed_columns == {}
        assert t.filter == []
        assert t.sort == []
        assert t.group_by is None
        assert t.pivot is None
        assert t.format == {}

    def test_groupModeExclusivity(self):
        gb = GroupBy(columns=["col1"], agg={"val": "sum"})
        pv = Pivot(index=["row"], columns=["col"], values="val", agg="sum")
        with pytest.raises(ValueError, match="Cannot use both 'group_by' and 'pivot'"):
            TableOptions(group_by=gb, pivot=pv)

    def test_groupByMissingAggRaises(self):
        gb = GroupBy(columns=["col1"], agg={})
        with pytest.raises(ValueError, match="'group_by' requires an 'agg' mapping"):
            TableOptions(group_by=gb)

    def test_pivotWithSortRaises(self):
        pv = Pivot(index=["row"], columns=["col"], values="val", agg="sum")
        sort_instr = [SortInstruction(column="val")]
        with pytest.raises(ValueError, match="Sorting a pivoted table is ambiguous"):
            TableOptions(pivot=pv, sort=sort_instr)
