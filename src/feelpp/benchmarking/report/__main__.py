from feelpp.benchmarking.dashboardRenderer.core.dashboard import Dashboard
from feelpp.benchmarking.report.parser import ReportArgParser

import os, subprocess, yaml

import feelpp.benchmarking
from feelpp.benchmarking.report.plugins.reframeReport import ReframeReportPlugin

class VersionPlugin:
    @staticmethod
    def process(template_data):
        return {"feelpp_benchmarking_version":feelpp.benchmarking.__version__}



def extractAntoraProjectName(antora_basepath):
    if not os.path.isdir(antora_basepath):
        raise FileNotFoundError(f"Could not find antora base path. Recieved: {antora_basepath}")

    with open(os.path.join(antora_basepath,"site.yml"),"r") as f:
        site_content = yaml.safe_load(f)

    sources = site_content['content']['sources']
    start_path = None

    for source in sources:
        if "HEAD" in source.get("branches"):
            start_path = source.get("start_path")

    if not start_path:
        raise ImportError("Could not find the start_path of the head branch in site.yml")

    antora_yml_path = os.path.join(antora_basepath,start_path,"antora.yml")
    with open(antora_yml_path,"r") as f:
        antora_yml = yaml.safe_load(f)

    project_name = antora_yml.get("name")

    if not project_name:
        raise ImportError(f"Could not find the name field inside in {antora_yml_path}")

    return project_name





def main_cli():
    parser = ReportArgParser()

    dashboard = Dashboard(
        parser.args.config_file,
        plugins=[ VersionPlugin ]
    )

    if parser.args.plot_configs:
        dashboard.patchTemplateInfo(parser.args.plot_configs, parser.args.patch_reports, "report", parser.args.save_patches)
    dashboard.print()


    #MOVE ELSEWHERE
    project_name = extractAntoraProjectName(parser.args.antora_basepath)

    dashboard.tree.upstreamViewData(ReframeReportPlugin.aggregator)
    dashboard.render(parser.args.module_path,clean=parser.args.reset_docs, project_name = project_name, include_latex_download=True)

    if parser.args.website:
        os.chdir(parser.args.antora_basepath)
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])
