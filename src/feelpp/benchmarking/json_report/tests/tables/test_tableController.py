import pytest
import pandas as pd
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import Table, FilterCondition, SortInstruction, GroupBy, Pivot,TableStyle
from feelpp.benchmarking.json_report.tables.controller import Controller


class TestTableController:

    @pytest.fixture
    def sampleDf(self):
        return pd.DataFrame({
            "id": [1, 2, 3, 4],
            "name": ["Alice", "Bob", "Charlie", "David"],
            "age": [25, 30, 35, 40],
            "score": [90, 80, 70, 60],
            "group": ["A", "B", "A", "B"]
        })

    # ------------------------------------------------------------------
    # Empty DataFrame
    # ------------------------------------------------------------------
    def test_emptyDataFrameReturnsEmpty(self):
        tableCfg = Table()
        ctrl = Controller(pd.DataFrame(), tableCfg)
        result = ctrl.generate()
        assert result.empty

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "filters,expectedIds",
        [
            ([FilterCondition(column="age", op=">", value=30)], [3, 4]),
            ([FilterCondition(column="group", op="==", value="A")], [1, 3]),
            ([FilterCondition(column="score", op="<=", value=80)], [2, 3, 4]),
            ([FilterCondition(column="id", op="in", value=[1,3])], [1, 3]),
            ([FilterCondition(column="id", op="not in", value=[2,4])], [1, 3]),
            ([FilterCondition(column="score", op="!=", value=70)], [1, 2, 4]),
            ([FilterCondition(column="age", op="<", value=35)], [1, 2]),
            ([FilterCondition(column="age", op=">=", value=30)], [2,3,4]),
            ([FilterCondition(column="score", op="<", value=80)], [3,4]),
            ([FilterCondition(column="score", op=">=", value=70)], [1,2,3]),
        ]
    )
    def test_filterOperators(self, sampleDf, filters, expectedIds):
        tableCfg = Table(filter=filters)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        assert result["id"].tolist() == expectedIds

    # ------------------------------------------------------------------
    # Column selection
    # ------------------------------------------------------------------
    @pytest.mark.parametrize( "columns,expectedColumns",
        [
            (["id", "name"], ["id", "name"]),
            (["score", "group"], ["score", "group"]),
            ([], ["id","name","age","score","group"])
        ]
    )
    def test_selectColumns(self, sampleDf, columns, expectedColumns):
        tableCfg = Table(columns=columns)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        assert list(result.columns) == expectedColumns

    # ------------------------------------------------------------------
    # Rename columns
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("rename,expectedColumns",
        [
            ({"name": "full_name"}, ["id","full_name","age","score","group"]),
            ({"score": "points", "group":"grp"}, ["id","name","age","points","grp"])
        ]
    )
    def test_renameColumns(self, sampleDf, rename, expectedColumns):
        tableCfg = Table(rename=rename)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        assert list(result.columns) == expectedColumns

    # ------------------------------------------------------------------
    # Computed columns
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("computed,expectedValues",
        [
            ({"double_score":"row['score']*2"}, [180,160,140,120]),
            ({"age_plus_score":"row['age']+row['score']"}, [115,110,105,100])
        ]
    )
    def test_computedColumns(self, sampleDf, computed, expectedValues):
        tableCfg = Table(computed_columns=computed)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        col = list(computed.keys())[0]
        assert result[col].tolist() == expectedValues

    # ------------------------------------------------------------------
    # GroupBy aggregation
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("groupCols,aggCfg,expectedScores",
        [
            (["group"], {"score":"mean"}, {"A":80,"B":70}),
            (["group"], "sum", {"A":160,"B":140})
        ]
    )
    def test_groupByAggregatesCorrectly(self, sampleDf, groupCols, aggCfg, expectedScores):
        gb = GroupBy(columns=groupCols, agg=aggCfg)
        tableCfg = Table(group_by=gb)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        for grp,val in expectedScores.items():
            assert result.loc[result["group"]==grp,"score"].values[0] == val

    # ------------------------------------------------------------------
    # Pivot tables
    # ------------------------------------------------------------------
    def test_pivotTables(self, sampleDf):
        pv = Pivot(index=["group"], columns=["name"], values="score", agg="sum")
        tableCfg = Table(pivot=pv)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        # columns should include pivoted names
        for n in ["Alice","Bob","Charlie","David"]:
            assert n in result.columns
        assert set(result["group"]) == {"A","B"}

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("sortCfg,expectedOrder",
        [
            ([SortInstruction(column="score", ascending=False)], [90,80,70,60]),
            ([SortInstruction(column="age", ascending=True)], [25,30,35,40])
        ]
    )
    def test_sorting(self, sampleDf, sortCfg, expectedOrder):
        tableCfg = Table(sort=sortCfg)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        assert result[sortCfg[0].column].tolist() == expectedOrder

    # ------------------------------------------------------------------
    # Column ordering
    # ------------------------------------------------------------------
    def test_columnOrdering(self, sampleDf):
        tableCfg = Table(column_order=["name","id","age"])
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        assert list(result.columns)[:3] == ["name","id","age"]

    # ------------------------------------------------------------------
    # Formatting numeric and mapping
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("fmt,expectedType",
        [
            ({"score":"%.1f"}, str),
            ({"group":{"A":"Alpha","B":"Beta"}}, str)
        ]
    )
    def test_formatting(self, sampleDf, fmt, expectedType):
        tableCfg = Table(format=fmt)
        ctrl = Controller(sampleDf, tableCfg)
        result = ctrl.generate()
        col = list(fmt.keys())[0]
        assert all(isinstance(v, expectedType) for v in result[col])

    # ------------------------------------------------------------------
    # getColsAlignment
    # ------------------------------------------------------------------
    def test_getColsAlignmentDefaults(self, sampleDf):
        tableCfg = Table(column_order=["id","name","score"])
        ctrl = Controller(sampleDf, tableCfg)
        colsStr = ctrl.getColsAlignment()
        assert colsStr == "<3,<3,<3"

    def test_getColsAlignmentCustom(self, sampleDf):
        style = TableStyle(**{
            "column_align":{"id":"right","score":"center"},
            "column_width":{"name":5}
        })
        tableCfg = Table(column_order=["id","name","score"], style=style)
        ctrl = Controller(sampleDf, tableCfg)
        colsStr = ctrl.getColsAlignment()
        assert colsStr == ">3,<5,^3"
