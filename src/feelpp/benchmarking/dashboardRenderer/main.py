from feelpp.benchmarking.dashboardRenderer.core.dashboard import Dashboard

dashboard = Dashboard(
    "src/feelpp/benchmarking/dashboardRenderer/dashboard_config.json",
    {"title":"My Dashboard"}
)

dashboard.builder.repositories.printViews()

dashboard.render("docs/modules/ROOT")