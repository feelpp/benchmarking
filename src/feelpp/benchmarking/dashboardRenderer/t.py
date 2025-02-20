from feelpp.benchmarking.dashboardRenderer.dashboardOrchestrator import DashboardOrchestrator
from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory
from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer
import json
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema

with open("src/feelpp/benchmarking/dashboardRenderer/dashboard_config.json","r") as f:
    components_config = DashboardSchema(**json.load(f))


orchestrator = DashboardOrchestrator(components_config, title="Benchmarking")
orchestrator.render("docs/modules/ROOT")



# print(json.dumps(views,indent=4))