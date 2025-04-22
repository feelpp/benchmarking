from feelpp.benchmarking.dashboardRenderer.core.dashboard import Dashboard
from feelpp.benchmarking.report.parser import ReportArgParser

import os, subprocess

from feelpp.benchmarking.report.plugins.reframeReport import ReframeReport


def main_cli():
    parser = ReportArgParser()
    parser.printArgs()

    dashboard = Dashboard(
        parser.args.config_file,
        plugins={
            "reframeRunsToDf":ReframeReport.runsToDf
        }
    )

    if parser.args.plot_configs:
        dashboard.patchTemplateInfo(parser.args.plot_configs, parser.args.patch_reports, "plots")

    dashboard.printViews()


    dashboard.render(parser.args.module_path,clean=True)

    if parser.args.website:
        os.chdir(parser.args.antora_basepath)
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])

main_cli()