from feelpp.benchmarking.json_report.renderer import Json2AdocRenderer

if __name__ == "__main__":
    renderer = Json2AdocRenderer( "./example_dashboard/fibonacci/Fibonacci/default/2025_11_21T11_53_57/report.json" )
    renderer.render("./fibonacci_report.adoc")