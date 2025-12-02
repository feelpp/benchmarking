import os, warnings, importlib.util, pytest, math, tempfile
from feelpp.benchmarking.json_report.schemas.jsonReport import *
from feelpp.benchmarking.json_report.schemas.dataRefs import Preprocessor




class TestReportNodes:

    # ------------------------------------------------------------------
    # TextNode creation
    # ------------------------------------------------------------------
    def test_textNodeCreation(self):
        node = TextNode(type="text", text=Text(content="hello"))
        assert node.text.content == "hello"
        assert node.type == "text"

    # ------------------------------------------------------------------
    # LatexNode creation
    # ------------------------------------------------------------------
    def test_latexNodeCreation(self):
        node = LatexNode(type="latex", latex="\\frac{1}{2}")
        assert node.latex == "\\frac{1}{2}"

    # ------------------------------------------------------------------
    # ImageNode creation
    # ------------------------------------------------------------------
    def test_imageNodeCreationOptionalFields(self):
        node = ImageNode(type="image", src="img.png", caption="cap", alt="alt")
        assert node.src == "img.png"
        assert node.caption == "cap"
        assert node.alt == "alt"

    # ------------------------------------------------------------------
    # ListNode coercion
    # ------------------------------------------------------------------
    def test_listNodeCoerceTextItems(self):
        text1 = Text(content="a")
        text2 = "b"
        items = [text1, text2]
        node = ListNode(type="itemize", items=items)
        assert all(isinstance(i, TextNode) for i in node.items)
        assert node.items[0].text.content == "a"
        assert node.items[1].text.content == "b"

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

    # ------------------------------------------------------------------
    # DataFile: coerceExpose
    # ------------------------------------------------------------------
    def test_dataFileCoerceExposeSetsName(self):
        with tempfile.NamedTemporaryFile(suffix=".csv") as tmp:
            df = DataFile.model_validate({"name":"data1", "filepath":tmp.name, "expose":True}, context={"report_filepath":tmp.name})
            assert df.expose == "data1"

    def test_dataFileCoerceExposeKeepsString(self):
        with tempfile.NamedTemporaryFile(suffix=".csv") as tmp:
            df = DataFile.model_validate({"name":"data1", "filepath":tmp.name, "expose":"custom"},context={"report_filepath":tmp.name})
            assert df.expose == "custom"

    # ------------------------------------------------------------------
    # DataFile: infer format
    # ------------------------------------------------------------------
    def test_dataFileInferFormatFromFilepath(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            df = DataFile.model_validate({"name":"data1", "filepath":tmp.name, "format":"json", "expose":"custom"},context={"report_filepath":tmp.name})
            assert df.format == "json"

    # ------------------------------------------------------------------
    # JsonReportSchema: coerce list input
    # ------------------------------------------------------------------
    def test_jsonReportSchemaCoerceListOfPlots(self):
        schema = JsonReportSchema.model_validate([
            {"title":"plot1", "plot_types":["scatter"], "xaxis":{"parameter":"x"}, "yaxis":{"parameter":"y"}},
            {"title":"plot2", "plot_types":["scatter"], "xaxis":{"parameter":"x2"}, "yaxis":{"parameter":"y2"}}
        ])
        assert isinstance(schema.contents[0], PlotNode) and isinstance(schema.contents[1], PlotNode)

    def test_jsonReportSchemaCoerceDictPassesThrough(self):
        schema = JsonReportSchema.model_validate({"title":"myreport"})
        assert schema.title == "myreport"

    def test_jsonReportSchemaCoerceListInvalidTypeRaises(self):
        with pytest.raises(ValidationError):
            JsonReportSchema.model_validate([{"test":"test"}])

    # ------------------------------------------------------------------
    # SectionNode flattenContent
    # ------------------------------------------------------------------
    def test_sectionNodeFlattenContent(self):
        textNode = TextNode(type="text", text=Text(content="a"))
        section = SectionNode(type="section", title="sec", contents=[textNode])
        schema = JsonReportSchema(contents=[section])
        flattened = schema.flattenContent()
        assert len(flattened) == 1
        assert flattened[0].text.content == "a"