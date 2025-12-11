import pytest
import pandas as pd
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import TableLayout, TableStyle
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
        ctrl = Controller(pd.DataFrame(), TableLayout(), TableStyle())
        result = ctrl.generate()
        assert result.empty

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
        ctrl = Controller(sampleDf, TableLayout(rename=rename), TableStyle())
        result = ctrl.generate()
        assert list(result.columns) == expectedColumns


    # ------------------------------------------------------------------
    # Column ordering and selection
    # ------------------------------------------------------------------
    def test_columnOrdering(self, sampleDf):
        ctrl = Controller(sampleDf, TableLayout(column_order=["name","id","age"]), TableStyle())
        result = ctrl.generate()
        assert list(result.columns) == ["name","id","age"]

    # ------------------------------------------------------------------
    # getColsAlignment
    # ------------------------------------------------------------------
    def test_getColsAlignmentDefaults(self, sampleDf):
        ctrl = Controller(sampleDf, TableLayout(column_order=["id","name","score"]), TableStyle() )
        colsStr = ctrl.getColsAlignment()
        assert colsStr == "<3,<3,<3"

    def test_getColsAlignmentCustom(self, sampleDf):
        style = TableStyle(**{
            "column_align":{"id":"right","score":"center"},
            "column_width":{"name":5}
        })
        layout = TableLayout(column_order=["id","name","score"])
        ctrl = Controller(sampleDf, layout, style)
        colsStr = ctrl.getColsAlignment()
        assert colsStr == ">3,<5,^3"
