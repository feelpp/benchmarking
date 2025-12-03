import pytest
import pandas as pd
import numpy as np

from feelpp.benchmarking.json_report.schemas.dataRefs import  *
from feelpp.benchmarking.json_report.dataLoader  import DataFieldParserFactory, DataTableParser, DataObjectParser, DataRawParser


# ------------------------------------------------------------
# DataFieldParserFactory Tests
# ------------------------------------------------------------

class TestDataFieldParserFactory:
    def test_create(self):
        dt = DataTable(name="dt",source=InlineTable(columns=[]))
        do = DataObject(name="do",source=InlineObject(object={}))
        dr = DataRaw(name="dr",source=InlineRaw(value="raw"))

        assert isinstance(DataFieldParserFactory.create(dt), DataTableParser)
        assert isinstance(DataFieldParserFactory.create(do), DataObjectParser)
        assert isinstance(DataFieldParserFactory.create(dr), DataRawParser)

    def test_raises(self):
        class UnknownField:
            type = "unknown"
        with pytest.raises(NotImplementedError):
            DataFieldParserFactory.create(UnknownField())


class TestDataRawParser:
    def test_loadInline(self):
        dr = DataRaw(name="rawdata",source=InlineRaw(value="hello"))
        parser = DataRawParser(dr)
        assert parser.load() == "hello"

    def test_loadFile(self, tmp_path):
        filepath = tmp_path / "data.txt"
        filepath.write_text("file contents")

        dr = DataRaw(name="rawdata",source=DataFile.model_validate(dict(filepath=str(filepath)),context={"report_filepath":str(filepath)}))
        parser = DataRawParser(dr)
        result = parser.load()

        assert result == "file contents"


    def test_loadInvalid(self):
        dr = DataRaw(source=InlineObject(object={}),name="dr")
        parser = DataRawParser(dr)
        with pytest.raises(NotImplementedError):
            parser.load()



class TestObjectParser:
    def test_loadInline(self):
        do = DataObject(name="objec_data", source=InlineObject(object={"a":"b","c":{"c1":"c2"}}))
        parser = DataObjectParser(do)
        assert parser.load() == {"a":"b","c":{"c1":"c2"}}

    def test_loadFileJson(self, tmp_path):
        filepath = tmp_path / "data.json"
        filepath.write_text("""{"a":"b","c":{"c1":"c2"}}""")

        dr = DataObject(name="object_data",source=DataFile.model_validate(dict(filepath=str(filepath)),context={"report_filepath":str(filepath)}))
        parser = DataObjectParser(dr)
        result = parser.load()

        assert isinstance(result,dict)
        assert result == {"a":"b","c":{"c1":"c2"}}

    def test_loadFileCsv(self, tmp_path):
        filepath = tmp_path / "data.csv"
        filepath.write_text("""a,b,c\n1,2,3\n11,22,33""")

        dr = DataObject(name="object_data",source=DataFile.model_validate(dict(filepath=str(filepath)),context={"report_filepath":str(filepath)}))
        parser = DataObjectParser(dr)
        result = parser.load()

        assert isinstance(result,dict)
        assert result == {"a":[1,11],"b":[2,22],"c":[3,33]}



    def test_loadInvalid(self,tmp_path):
        with pytest.raises(UserWarning):
            dr = DataObject(name="object_data",source=DataFile.model_validate(dict(filepath=str(tmp_path)),context={"report_filepath":str(tmp_path)}))
            parser = DataObjectParser(dr)
            with pytest.raises(NotImplementedError):
                result = parser.load()

        dr = DataObject(source=InlineRaw(value=""),name="dr")
        parser = DataObjectParser(dr)
        with pytest.raises(NotImplementedError):
            parser.load()

class TestDataTableParser:

    def test_loadInlineTable(self):
        dt = DataTable( name="table",
            source=InlineTable(columns=[
                InlineTableColumn(name="a", values=[1, 2, 3]),
                InlineTableColumn(name="b", values=[10, 20, 30])
            ])
        )
        parser = DataTableParser(dt)
        df = parser.load()

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["a", "b"]
        assert list(df["a"]) == [1, 2, 3]
        assert list(df["b"]) == [10, 20, 30]

    def test_loadCsv(self,tmp_path):
        filepath = tmp_path / "data.csv"
        filepath.write_text("a,b\n1,2\n3,4\n")

        dt = DataTable( name="table", source=DataFile.model_validate( dict(filepath=str(filepath), format="csv"), context={"report_filepath": str(filepath)} ) )
        parser = DataTableParser(dt)
        df = parser.load()

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["a", "b"]
        assert list(df["a"]) == [1, 3]
        assert list(df["b"]) == [2, 4]


    def test_loadJson(self, tmp_path):
        filepath = tmp_path / "data.json"
        filepath.write_text('[{"x": 1, "y": 2}, {"x": 3, "y": 4}]')

        dt = DataTable( name="table", source=DataFile.model_validate( dict(filepath=str(filepath), format="json"), context={"report_filepath": str(filepath)} ) )
        parser = DataTableParser(dt)
        df = parser.load()

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["x", "y"]
        assert list(df["x"]) == [1, 3]

    def test_loadUnsupportedFormat(self,tmp_path):
        filepath = tmp_path / "data.txt"
        filepath.write_text("invalid")

        dt = DataTable( name="table", source=DataFile.model_validate( dict(filepath=str(filepath)), context={"report_filepath": str(filepath)} ) )
        parser = DataTableParser(dt)

        with pytest.raises(NotImplementedError):
            parser.load()


    def test_loadInvalidInlineTypeRaises(self):
        dt = DataTable( name="table", source=InlineObject(object={"bad": "type"}) )
        parser = DataTableParser(dt)

        with pytest.raises(NotImplementedError):
            parser.load()

    @staticmethod
    def makeParser() -> DataTableParser:
        """Create a DataTableParser instance without calling __init__()."""
        return DataTableParser.__new__(DataTableParser)


    def test_applyFilter(self):
        df = pd.DataFrame({ "a": [1, 2, 3, 4],"b": ["x", "y", "x", "y"] })

        filters = [
            FilterCondition(column="a", op=">", value=2),
            FilterCondition(column="b", op="==", value="y"),
        ]

        parser = self.makeParser()
        out = parser._applyFilter(filters, df)

        assert len(out) == 1
        assert out.iloc[0].a == 4
        assert out.iloc[0].b == "y"


    def test_computeColumns(self):
        df = pd.DataFrame({ "x": [1, 2, 3], "y": [10, 20, 30] })

        computed = { "z": "row['x'] + row['y']", "t": "row['x'] * 2", }

        parser = self.makeParser()
        out = parser._computeColumns(computed, df)

        assert list(out.columns) == ["x", "y", "z", "t"]
        assert out["z"].tolist() == [11, 22, 33]
        assert out["t"].tolist() == [2, 4, 6]


    def test_pivot(self):
        df = pd.DataFrame({
            "team": ["A", "A", "B", "B"],
            "metric": ["m1", "m2", "m1", "m2"],
            "value": [10, 20, 30, 40]
        })

        pivot = Pivot(
            index=["team"],
            columns=["metric"],
            values="value",
            agg="mean"
        )

        parser = self.makeParser()
        out = parser._pivot(pivot, df)

        assert list(out.columns) == ["team", "m1", "m2"]
        assert out.loc[out.team == "A", "m1"].iloc[0] == 10
        assert out.loc[out.team == "B", "m2"].iloc[0] == 40


    def test_groupAndAggregate(self):
        df = pd.DataFrame({
            "grp": ["x", "x", "y", "y"],
            "val1": [1, 2, 3, 4],
            "val2": [10, 20, 30, 40]
        })

        groupby = GroupBy(
            columns=["grp"],
            agg="sum"   # string form must apply to all non-groupby columns
        )

        parser = self.makeParser()
        out = parser._groupAndAggregate(groupby, df)

        assert list(out.columns) == ["grp", "val1", "val2"]
        assert out[out.grp == "x"].val1.iloc[0] == 3
        assert out[out.grp == "y"].val2.iloc[0] == 70



    def test_sort(self):
        df = pd.DataFrame({
            "a": [3, 1, 2],
            "b": [9, 8, 7]
        })

        sort = [
            SortInstruction(column="a", ascending=True)
        ]

        parser = self.makeParser()
        out = parser._sort(sort, df)

        assert out["a"].tolist() == [1, 2, 3]

    def test_format(self):
        df = pd.DataFrame({
            "num": [1.234, 5.678],
            "code": ["A", "B"]
        })

        fmt = {
            "num": "%.1f",
            "code": {"A": "Alpha", "B": "Beta"}
        }

        parser = self.makeParser()
        out = parser._format(fmt, df)

        assert out["num"].tolist() == ["1.2", "5.7"]
        assert out["code"].tolist() == ["Alpha", "Beta"]




    @pytest.mark.parametrize( "options, expected", [
        # FILTER
        (
            dict( filter=[FilterCondition(column="a", op=">", value=1)]),
            pd.DataFrame({"a": [2, 3], "b": [20, 30], "c":[ 200,300 ]})
        ),
        # COMPUTED COLUMNS
        (
            dict( computed_columns={"d": "row['a'] + row['b']"} ),
            pd.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30], "c":[100,200,300],"d": [11, 22, 33]})
        ),

        # GROUP BY
        (
            dict( group_by=GroupBy(columns=["b"], agg="sum") ),
            pd.DataFrame({"b": [10, 20, 30], "a": [1, 2, 3], "c":[100,200,300]})
        ),

        # PIVOT
        (
            dict( pivot=Pivot( index=["a"], columns=["b"], values="c", agg="mean" ) ),
            # expected pivot result
            pd.DataFrame( {
                "a": [1, 2, 3],
                10: [100, np.nan, np.nan],
                20: [np.nan, 200, np.nan],
                30: [np.nan, np.nan, 300],
            } )
        ),

        # SORT
        (
            dict( sort=[SortInstruction(column="b", ascending=False)] ),
            pd.DataFrame({"a": [3, 2, 1], "b": [30, 20, 10],"c":[300,200,100]})
        ),

        # FORMAT
        (
            dict( format={"b": "%.1f"} ),
            pd.DataFrame({"a": [1, 2, 3], "b": ["10.0", "20.0", "30.0"],"c":[100,200,300]})
        )
    ])
    def test_process(self,options,expected):
        dt = DataTable(
            name="table",
            source=InlineTable(columns=[
                InlineTableColumn(name="a", values=[1, 2, 3]),
                InlineTableColumn(name="b", values=[10, 20, 30]),
                InlineTableColumn(name="c", values=[100, 200, 300]),
            ])
        )

        dt.table_options = TableOptions(**options)

        parser = DataTableParser(dt)
        df = parser.load()
        out = parser.process(df)

        out = out.reset_index(drop=True)
        expected = expected.reset_index(drop=True)
        assert list(out.columns) == list(expected.columns)
        pd.testing.assert_frame_equal(out, expected, check_dtype=False,check_names=False)