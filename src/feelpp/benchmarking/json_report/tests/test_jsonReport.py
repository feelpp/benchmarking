import pytest, os, tempfile, difflib, json, re
from feelpp.benchmarking.json_report.renderer import JsonReportController


def normalizeReport(content: str) -> str:
    content = content.strip()

    content = re.sub( r"^:docdatetime: .*?$", ":docdatetime: <TIMESTAMP>", content, flags=re.MULTILINE )

    content = re.sub(
        r"<button[^>]*?>\s*(.*?)\s*</button>",
        lambda match : f"<button>{match.group(1).strip()}</button>",
        content, flags=re.DOTALL
    )
    content = re.sub(
        r"<div[^>]*>\s*<div[^>]*></div>\s*<script.*?</script>\s*</div>",
        """
        <div>
            <div>FIGURE</div>
            <script></script>
        </div>""",
        content,
        flags=re.DOTALL
    )

    lines = [line.rstrip() for line in content.splitlines() if line.strip()]
    return "\n".join(lines)


def assert_report_matches_golden(output_file: str, golden_file: str):
    with open(output_file, "r") as f:
        output_content = normalizeReport(f.read())
    with open(golden_file, "r") as f:
        golden_content = normalizeReport(f.read())

    if output_content != golden_content:
        diff = "\n".join(
            difflib.unified_diff( golden_content.splitlines(), output_content.splitlines(),
                                 fromfile="golden",tofile="output", lineterm="" )
        )
        print(diff)
        pytest.fail("Generated report does not match golden file")



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
        output_file = controller.render(output_dirpath=os.path.join(data_dir,tmpdir))
        golden_file = os.path.join(data_dir,"golden",report_filename.replace(".json",f".{output_format}"))
        assert_report_matches_golden(output_file,golden_file)