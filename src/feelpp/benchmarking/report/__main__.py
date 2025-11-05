from feelpp.benchmarking.dashboardRenderer.core.dashboard import Dashboard
from feelpp.benchmarking.report.parser import ReportArgParser

import os, subprocess

from feelpp.benchmarking.report.plugins.reframeReport import ReframeReportPlugin


def main_cli():
    parser = ReportArgParser()
    parser.printArgs()

    dashboard = Dashboard(
        parser.args.config_file,
        plugins={
            "reframe_runs_df":ReframeReportPlugin
        }
    )

    if parser.args.plot_configs:
        dashboard.patchTemplateInfo(parser.args.plot_configs, parser.args.patch_reports, "plots", parser.args.save_patches)

    dashboard.printViews()

    dashboard.upstreamView()
    dashboard.render(parser.args.module_path,clean=parser.args.reset_docs)

    if parser.args.website:
        os.chdir(parser.args.antora_basepath)
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])
