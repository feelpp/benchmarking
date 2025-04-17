from feelpp.benchmarking.dashboardRenderer.core.dashboard import Dashboard

from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer
from feelpp.benchmarking.dashboardRenderer.plugins.reframeReport import ReframeReport

TemplateRenderer.plugins["reframeRunsToDf"] = ReframeReport.runsToDf

dashboard = Dashboard(
    "src/feelpp/benchmarking/dashboardRenderer/dashboard_config.json",
    {"title":"My Dashboard"}
)

dashboard.printViews()

dashboard.render("docs/modules/ROOT",clean=True)