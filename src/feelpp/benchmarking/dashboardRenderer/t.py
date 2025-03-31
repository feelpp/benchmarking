from dashboardOrchestrator import DashboardOrchestrator
from controller import BaseControllerFactory
from renderer import TemplateRenderer
import json
from schemas.dashboardSchema import DashboardSchema

with open("src/feelpp/benchmarking/dashboardRenderer/dashboard_config.json","r") as f:
    components_config = DashboardSchema(**json.load(f))


orchestrator = DashboardOrchestrator(components_config, title="Benchmarking")
orchestrator.render("docs/modules/ROOT")



# print(json.dumps(views,indent=4))