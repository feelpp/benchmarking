import json, os, pytest, warnings
import pandas as pd
from unittest.mock import MagicMock, patch

from feelpp.benchmarking.json_report.schemas.jsonReport import JsonReportSchema, DataFile,Preprocessor
from feelpp.benchmarking.json_report.renderer import JsonReportController



# ----------------------------------------------------------------------
# loadReport()
# ----------------------------------------------------------------------
@pytest.mark.parametrize("exists", [True, False])
def test_loadReportReturnsEmptySchemaIfMissing(tmp_path, exists):
    json_path = tmp_path / "report.json"

    if exists:
        json_path.write_text(json.dumps({"title": "hello"}))

    ctrl = JsonReportController.__new__(JsonReportController)  # bypass __init__
    if exists:
        out = ctrl.loadReport(str(json_path))
        assert isinstance(out, JsonReportSchema)
        assert out.title == "hello"
    else:
        with pytest.raises(UserWarning):
            out = ctrl.loadReport(str(json_path))
            assert isinstance(out, JsonReportSchema)
            assert out.title is None


# ----------------------------------------------------------------------
# getTemplatePath()
# ----------------------------------------------------------------------
def test_getTemplatePathAdoc(tmp_path):
    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.output_format = "adoc"

    template_dir, template_filename = ctrl.getTemplatePath()

    assert template_filename == "json2adoc_report.adoc.j2"
    assert os.path.isdir(template_dir)


def test_getTemplatePathUnsupportedFormat():
    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.output_format = "foo"

    with pytest.raises(ValueError):
        ctrl.getTemplatePath()


# ----------------------------------------------------------------------
# initRenderer()
# ----------------------------------------------------------------------
def test_initRendererCreatesRendererAndInjectsControllers(monkeypatch):
    class FakeRenderer:
        def __init__(self, template_paths=None, template_filename=None):
            self.env = MagicMock()
            self.env.globals = {}

        def render(self, *args, **kwargs):
            pass

    monkeypatch.setattr( "feelpp.benchmarking.json_report.renderer.TemplateRenderer", FakeRenderer )
    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.output_format = "adoc"

    # Stub getTemplatePath so we don't care about files
    monkeypatch.setattr(
        ctrl, "getTemplatePath",
        lambda: ("/tmp", "template.j2")
    )

    renderer = ctrl.initRenderer()

    assert isinstance(renderer, FakeRenderer)
    assert "FiguresController" in renderer.env.globals
    assert "TableController" in renderer.env.globals
    assert "TextController" in renderer.env.globals

# ----------------------------------------------------------------------
# loadReportData()
# ----------------------------------------------------------------------
def test_loadReportDataLoadsJson(tmp_path):
    # Create a fake JSON data file
    datafile_path = tmp_path / "data.json"
    datafile_path.write_text(json.dumps({"a": 1}))

    # Build fake report schema
    df = DataFile(
        name="d1",
        filepath=str(datafile_path),
        format="json",
        expose=True
    )

    report = JsonReportSchema(
        data=[df]
    )

    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.report = report
    ctrl.exposed = {}

    data = ctrl.loadReportData()

    assert "d1" in data
    assert data["d1"] == {"a": 1}
    assert ctrl.exposed["d1"] == {"a": 1}


def test_loadReportDataLoadsCsv(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("x,y\n1,2\n3,4\n")

    df = DataFile( name="tab", filepath=str(csv_path), format="csv", expose=False)

    report = JsonReportSchema(data=[df])

    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.report = report
    ctrl.exposed = {}

    data = ctrl.loadReportData()

    assert "tab" in data
    assert isinstance(data["tab"], pd.DataFrame)


def test_loadReportDataLoadsRaw(tmp_path):
    raw_path = tmp_path / "data.raw"
    raw_path.write_text("hello world")

    df = DataFile( name="rawfile", filepath=str(raw_path), format="raw", expose="alias")

    report = JsonReportSchema(data=[df])

    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.report = report
    ctrl.exposed = {}

    data = ctrl.loadReportData()

    assert data["rawfile"] == "hello world"
    assert ctrl.exposed["alias"] == "hello world"

def test_loadReportDataAppliesPreprocessor_withMock(tmp_path):
    raw_path = tmp_path / "data.raw"
    raw_path.write_text("hello")

    mock_prep = MagicMock()
    mock_prep.apply = MagicMock(return_value="processed")

    df = DataFile.model_construct( name = "d1", filepath=str(raw_path), format="raw", preprocessor=mock_prep, expose=False )

    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.report = type("R", (), {"data": [df]})()
    ctrl.exposed = {}

    data = JsonReportController.loadReportData(ctrl)

    mock_prep.apply.assert_called_once()
    assert data["d1"] == "processed"


# ----------------------------------------------------------------------
# render()
# ----------------------------------------------------------------------
def test_renderWritesToOutput(tmp_path):
    fake_renderer = MagicMock()
    fake_renderer.render = MagicMock()

    ctrl = JsonReportController.__new__(JsonReportController)
    ctrl.report_filepath = "report.json"
    ctrl.output_format = "adoc"
    ctrl.renderer = fake_renderer
    ctrl.report = JsonReportSchema()
    ctrl.data = {}

    output_dir = tmp_path
    result = ctrl.render(str(output_dir))

    expected_output = os.path.join(str(output_dir), "report.adoc")

    fake_renderer.render.assert_called_once()
    assert os.path.abspath(expected_output) == result
