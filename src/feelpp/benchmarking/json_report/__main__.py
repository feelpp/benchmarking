from feelpp.benchmarking.json_report.renderer import JsonReportController

if __name__ == "__main__":
    renderer = JsonReportController( "./example_dashboard/fibonacci/Fibonacci/default/2025_11_21T11_53_57/report.json" )
    renderer.render("./fibonacci_report.adoc")