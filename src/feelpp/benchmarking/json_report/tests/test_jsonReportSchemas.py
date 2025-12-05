import pytest
from feelpp.benchmarking.json_report.schemas.jsonReport import *


class ReportNodeTests:
    def test_creation(self):
        raise NotImplementedError(" test_creation Test should be implemented in derived classes")

    def test_coercion(self):
        raise NotImplementedError(" test_coercion Test should be implemented in derived classes")

    def test_defaults(self):
        raise NotImplementedError(" test_defaults Test should be implemented in derived classes")

    def test_raises(self):
        raise NotImplementedError(" test_raises Test should be implemented in derived classes")


class TestTextNode(ReportNodeTests):
    def test_creation(self):
        node = TextNode(type="text", text=Text(content="hello"))
        assert node.text.content == "hello"
        assert node.type == "text"

    def test_coercion(self):
        node = TextNode.model_validate({"type": "text", "text": "abc"})
        assert isinstance(node.text, Text)
        assert node.text.content == "abc"

    def test_defaults(self):
        #No defaults
        pass

    def test_raises(self):
        with pytest.raises(ValidationError):
            node = TextNode.model_validate({"type": "text"})


class TestLatexNode(ReportNodeTests):
    def test_creation(self):
        node = LatexNode(type="latex", latex="\\frac{1}{2}")
        assert node.latex == "\\frac{1}{2}"

    def test_defaults(self):
        #No defaults
        pass

    def test_coercion(self):
        #Not currently coerced
        pass

    def test_raises(self):
        with pytest.raises(ValidationError):
            node = TextNode.model_validate({"type": "latex"})


class TestImageNode(ReportNodeTests):
    def test_creation(self):
        node = ImageNode(type="image", src="img.png", caption="cap", alt="alt")
        assert node.src == "img.png"
        assert node.caption == "cap"
        assert node.alt == "alt"

    def test_coercion(self):
        #Not currenlty coerced
        pass

    def test_defaults(self):
        node = ImageNode.model_validate({"type": "image", "src": "img.png"})
        assert node.src == "img.png"
        assert node.caption is None
        assert node.alt is None

    def test_raises(self):
        with pytest.raises(ValidationError):
            node = ImageNode.model_validate({"type": "image"})


class TestListNode(ReportNodeTests):
    def test_creation(self):
        node = ListNode(type="itemize",items=["a","b","c"])
        assert node.items == [ TextNode(type="text",text=x) for x in ["a","b","c"]]

    def test_coercion(self):
        text1 = Text(content="a")
        text2 = "b"
        text3 = {"content":"c","placeholder":"@@([^}]+)@@"}
        text4 = TextNode(type="text",text=Text(content="d"))
        text5 = {"type":"text","text":"e"}

        node = ListNode(type="itemize", items=[text1, text2, text3, text4, text5])

        assert all(isinstance(i, TextNode) for i in node.items)
        assert node.items[0].text.content == "a"
        assert node.items[1].text.content == "b"
        assert node.items[2].text.content == "c"
        assert node.items[3].text.content == "d"
        assert node.items[4].text.content == "e"

    def test_defaults(self):
        #No defaults
        pass

    def test_raises(self):
        with pytest.raises(ValidationError):
            node = ListNode(type="itemize")
        with pytest.raises(ValidationError): #type should not be list
            node = ListNode(type="list",items=["a","b","c"])


class TestSectionNode(ReportNodeTests):
    def test_creation(self):
        node = SectionNode(type="section", title="My Title", contents=[ TextNode(type="text", text=Text(content="hello")) ])
        assert node.type == "section"
        assert node.title == "My Title"
        assert len(node.contents) == 1
        assert isinstance(node.contents[0], TextNode)

    def test_coercion(self):
        node = SectionNode.model_validate({
            "type": "section",
            "title": "Sec",
            "contents": [
                {"type": "text", "text": "hello"},
                {"type": "latex", "latex": "world"}
            ]
        })

        assert isinstance(node.contents[0], TextNode)
        assert node.contents[0].text.content == "hello"
        assert isinstance(node.contents[1], LatexNode)
        assert node.contents[1].latex == "world"

    def test_defaults(self):
        #No defaults
        pass

    def test_raises(self):
        with pytest.raises(ValidationError):
            node = SectionNode(type="section")

class TestTableNode(ReportNodeTests):

    def test_creation(self):
        node = TableNode(type="table")
        assert isinstance(node.layout, TableLayout)
        assert isinstance(node.style, TableStyle)
        assert node.filter is None

    def test_defaults(self):
        node1 = TableNode(type="table")
        node2 = TableNode(type="table")

        # Ensure defaults are not shared (mutable defaults)
        assert node1.style is not node2.style
        assert node1.style.column_align is not node2.style.column_align
        assert node1.style.column_width is not node2.style.column_width
        assert node1.style.classnames is not node2.style.classnames

    def test_coercion(self):
        # No coercion currently happens, but we test that direct assignment works
        node = TableNode(type="table", layout=TableLayout(), style=TableStyle(), filter=FilterInput())
        assert isinstance(node.layout, TableLayout)
        assert isinstance(node.style, TableStyle)
        assert isinstance(node.filter, FilterInput)

    def test_raises(self):
        pass


class TestPlotNode(ReportNodeTests):

    def test_creation(self):
        plot = Plot(title="p", plot_types=["scatter"], xaxis={"parameter": "x"}, yaxis={"parameter":"y"})
        node = PlotNode(type="plot", plot=plot)
        assert node.plot.title == "p"

    def test_coercion(self):
        data = {
            "type": "plot",
            "plot": {
                "title":"p",
                "plot_types":["scatter"],
                "xaxis":{"parameter":"x"},
                "yaxis":{"parameter":"y"}
            }
        }
        node = PlotNode.model_validate(data)
        assert isinstance(node.plot, Plot)
        assert node.plot.title == "p"

    def test_defaults(self):
        # No defaults in PlotNode
        pass

    def test_raises(self):
        with pytest.raises(ValidationError):
            PlotNode(type="plot")



class TestJsonReportSchema(ReportNodeTests):

    def test_creation(self):
        schema = JsonReportSchema.model_validate({"title": "report", "contents": []})
        assert schema.title == "report"
        assert schema.contents == []
        # datetime is auto-filled
        assert isinstance(schema.datetime, str) and len(schema.datetime) > 0


    def test_coercion(self):
        data = {
            "contents": [
                {"type": "text", "text": {"content": "hello"}},
                {"type": "latex", "latex": "\\alpha"}
            ]
        }
        schema = JsonReportSchema.model_validate(data)
        assert type(schema.contents[0]).__name__ == "TextNode"
        assert type(schema.contents[1]).__name__ == "LatexNode"
        assert schema.contents[0].text.content == "hello"
        assert schema.contents[1].latex == "\\alpha"


    def test_defaults(self):
        schema = JsonReportSchema.model_validate({})
        assert schema.data == []
        assert isinstance(schema.datetime, str)

    def test_raises(self):
        with pytest.raises(ValidationError):
            JsonReportSchema.model_validate({"contents": [{}]})

        with pytest.raises(ValidationError):
            JsonReportSchema.model_validate({"title":[]})


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


    def test_sectionNodeFlattenContent(self):
        textNode = TextNode(type="text", text=Text(content="a"))
        section = SectionNode(type="section", title="sec", contents=[textNode])
        schema = JsonReportSchema(contents=[section])
        flattened = schema.flattenContent()
        assert len(flattened) == 1
        assert flattened[0].text.content == "a"


    def test_sectionNodeDeepFlatten(self):
        inner = SectionNode( type="section", title="inner", contents=[TextNode(type="text", text=Text(content="x"))] )
        outer = SectionNode( type="section", title="outer", contents=[inner] )
        schema = JsonReportSchema(contents=[outer])
        flat = schema.flattenContent()
        assert len(flat) == 1
        assert flat[0].text.content == "x"


    def test_extraFieldsAllowed(self):
        schema = JsonReportSchema.model_validate({"foo": 123})
        assert schema.foo == 123
        schema = JsonReportSchema.model_validate({"title": "x", "bar": {"a": 1}})
        assert schema.bar == {"a": 1}

class TestRefPropagation:

    def test_listNodeRefPropagation(self):
        node = ListNode(type="itemize", ref="R", items=["a", "b"])
        assert node.items[0].ref == "R"
        assert node.items[1].ref == "R"

    def test_listNodeRefPriority(self):
        t = TextNode(type="text", text=Text(content="a"), ref="X")
        node = ListNode(type="itemize", ref="R", items=[t])
        assert node.items[0].ref == "X"  # user-specified ref takes priority
