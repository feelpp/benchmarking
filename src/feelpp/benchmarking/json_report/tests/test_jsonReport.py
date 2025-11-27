import pytest, os, tempfile
from feelpp.benchmarking.json_report.renderer import JsonReportController

@pytest.mark.parametrize("report_filename",
    ["basic_text.json", "list_with_data.json", "table_features.json", "plot_features.json","preprocessor.json","report.json" ]
)
def test_jsonReportCases(report_filename,output_format="adoc"):
    data_dir = os.path.join(os.path.dirname(__file__),"data")
    controller = JsonReportController(
        report_filepath=os.path.join(data_dir,report_filename),
        output_format=output_format
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        controller.render(output_dirpath=os.path.join(tmpdir,"outputs"))

        #CHECK tmpdir outputs match expected