import pytest
import pandas as pd
import numpy as np

from feelpp.benchmarking.json_report.schemas.dataRefs import  *
from feelpp.benchmarking.json_report.dataLoader  import DataLoaderFactory, DataProcessorFactory, DataTableProcessor, DataObjectProcessor, DataRawProcessor, DataFileLoader, InlineLoader


# ------------------------------------------------------------
# DataLoader Tests
# ------------------------------------------------------------
class TestDataLoaderFactory:
    def test_create(self,tmp_path):
        filepath = tmp_path / "data.json"
        filepath.write_text("")
        djson = DataField.model_validate(dict(name="test", source = dict(filepath=str(filepath))),context={"report_filepath":str(filepath)})
        assert isinstance(DataLoaderFactory.create(djson.source), DataFileLoader)

        dt = DataTable(name="dt",source=InlineTable(columns=[]))
        assert isinstance(DataLoaderFactory.create(dt.source), InlineLoader)

        do = DataObject(name="do",source=InlineObject(object={}))
        assert isinstance(DataLoaderFactory.create(do.source), InlineLoader)

        dr = DataRaw(name="dr",source=InlineRaw(value="raw"))
        assert isinstance(DataLoaderFactory.create(dr.source), InlineLoader)


class TestFileLoader:

    @pytest.mark.parametrize("extension,data,expected_type",[
        ("json", '{"my_obj":"my_val"}',dict),
        ("json", "{}",dict),
        ("txt","",str),
        ("txt","Some raw text",str),
        ("csv","a,b,c\n1,2,3",pd.DataFrame)
    ])
    def test_format(self,tmp_path,extension,data, expected_type):
        filepath = tmp_path / ("data." + extension)
        filepath.write_text(data)
        datafield = DataField.model_validate(dict(name="test", source = dict(filepath=str(filepath))),context={"report_filepath":str(filepath)})
        loaded = DataFileLoader(datafield.source).load()
        assert isinstance(loaded,expected_type)

    def test_unkown(self,tmp_path):
        filepath = tmp_path / "data.unkown"
        filepath.write_text("Weird format")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            datafield = DataField.model_validate(dict(name="test", source = DataFile(filepath=str(filepath))),context={"report_filepath":str(filepath)})
            datafield.source.format = "unkown"
            with pytest.raises(NotImplementedError):
                loaded = DataFileLoader(datafield.source).load()


    @pytest.mark.parametrize("content",[
        "file contents"
    ])
    def test_loadRaw(self, tmp_path,content):
        filepath = tmp_path / "data.txt"
        filepath.write_text(content)
        source=DataFile.model_validate(dict(filepath=str(filepath)),context={"report_filepath":str(filepath)})
        parser = DataFileLoader(source)
        assert parser.load() == content


    @pytest.mark.parametrize("content,expected",[
        ("""{"a":"b","c":{"c1":"c2"}}""", {"a":"b","c":{"c1":"c2"}})
    ])
    def test_loadJson(self, tmp_path,content,expected):
        filepath = tmp_path / "data.json"
        filepath.write_text(content)
        source=DataFile.model_validate(dict(filepath=str(filepath)),context={"report_filepath":str(filepath)})
        parser = DataFileLoader(source)
        assert parser.load() == expected


    @pytest.mark.parametrize("content,expected",[
        ("""a,b,c\n1,2,3\n11,22,33""", pd.DataFrame(columns=["a","b","c"],data=[[1,2,3],[11,22,33]]))
    ])
    def test_loadCsv(self, tmp_path,content,expected):
        filepath = tmp_path / "data.csv"
        filepath.write_text(content)
        source=DataFile.model_validate(dict(filepath=str(filepath)),context={"report_filepath":str(filepath)})
        parser = DataFileLoader(source)
        pd.testing.assert_frame_equal(parser.load(),expected)

class TestInlineLoader:

    @pytest.mark.parametrize("source, expected_type",[
        (
            InlineTable(columns=[ InlineTableColumn(name="a", values=[1, 2, 3]), InlineTableColumn(name="b", values=[10, 20, 30]) ]),
            pd.DataFrame
        ),
        ( InlineObject(object={"my_object":"val"}), dict ),
        ( InlineRaw(value="my_raw_str"), str ),
    ])
    def test_inlineTypes(self, source, expected_type):
        loaded = InlineLoader(source).load()
        assert isinstance(loaded,expected_type)


    @pytest.mark.parametrize("val", [
        "hello"
    ])
    def test_loadRaw(self,val):
        source = InlineRaw(value=val)
        loader = InlineLoader(source)
        assert loader.load() == val

    @pytest.mark.parametrize("val",[
        {"a":"b","c":{"c1":"c2"}}
    ])
    def test_loadJson(self,val):
        source =InlineObject(object=val)
        parser = InlineLoader(source)
        assert parser.load() == val

    def test_loadInlineTable(self):
        source=InlineTable(columns=[
            InlineTableColumn(name="a", values=[1, 2, 3]),
            InlineTableColumn(name="b", values=[10, 20, 30])
        ])
        parser = InlineLoader(source)
        df = parser.load()

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["a", "b"]
        assert list(df["a"]) == [1, 2, 3]
        assert list(df["b"]) == [10, 20, 30]

# ------------------------------------------------------------
# DataProcessor Tests
# ------------------------------------------------------------


class TestDataObjectProcessor:
    @pytest.mark.parametrize("input_data, expected", [
        (pd.DataFrame({"a": [1, 2]}), {"a": [1, 2]}), # DataFrame → dict(list)
        ('{"x": 1, "y": 2}', {"x": 1, "y": 2}), # JSON string → dict
        ({"k": 5}, {"k": 5}), # dict → unchanged
    ])
    def test_process(self,input_data,expected):
        p = DataObjectProcessor(DataObject(name="obj",preprocessor=None,source = InlineObject(object={})))
        assert p.process(input_data) == expected

class TestDataRawProcessor:
    @pytest.mark.parametrize("input_data, expected", [
        (pd.DataFrame({"a": [1]}), pd.DataFrame({"a":[1]}).to_string()), # DataFrame → string table
        ({"x": 7}, '{"x": 7}'),# dict → JSON string
        ("hello!", "hello!"), # string → unchanged
    ])
    def test_process(self,input_data, expected):
        p = DataRawProcessor(DataRaw(name="r",preprocessor=None, source=InlineRaw(value="")))
        assert p.process(input_data) == expected



class TestDataTableProcessor:

    def test_castJson(self):
        dt = DataTable( name="table", source=InlineTable(columns=[]) )
        parser = DataTableProcessor(dt)
        data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        df = parser.process(data)

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["x", "y"]
        assert list(df["x"]) == [1, 3]


    @staticmethod
    def makeProcessor() -> DataTableProcessor:
        """Create a DataTableProcessor instance without calling __init__()."""
        return DataTableProcessor.__new__(DataTableProcessor)


    def test_applyFilter(self):
        df = pd.DataFrame({ "a": [1, 2, 3, 4],"b": ["x", "y", "x", "y"] })

        filters = [
            FilterCondition(column="a", op=">", value=2),
            FilterCondition(column="b", op="==", value="y"),
        ]

        parser = self.makeProcessor()
        out = parser._applyFilter(filters, df)

        assert len(out) == 1
        assert out.iloc[0].a == 4
        assert out.iloc[0].b == "y"


    def test_computeColumns(self):
        df = pd.DataFrame({ "x": [1, 2, 3], "y": [10, 20, 30] })

        computed = { "z": "row['x'] + row['y']", "t": "row['x'] * 2", }

        parser = self.makeProcessor()
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

        parser = self.makeProcessor()
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

        parser = self.makeProcessor()
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

        parser = self.makeProcessor()
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

        parser = self.makeProcessor()
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
        dt = DataTable( name="table", source=InlineTable(columns=[ ]) )
        df = pd.DataFrame.from_dict({
            "a":[1,2,3],
            "b":[10,20,30],
            "c":[100,200,300]
        })

        dt.table_options = TableOptions(**options)

        parser = DataTableProcessor(dt)
        out = parser.process(df)

        out = out.reset_index(drop=True)
        expected = expected.reset_index(drop=True)
        assert list(out.columns) == list(expected.columns)
        pd.testing.assert_frame_equal(out, expected, check_dtype=False,check_names=False)