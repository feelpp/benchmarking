from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo
from feelpp.benchmarking.dashboardRenderer.views.base import View

class HomeView(View):
    def __init__(self, template_info: TemplateInfo):
        super().__init__(template_info)

    def render(self,output_dirpath):
        super().render(output_dirpath,"index.adoc")


    def initRenderer(self,template = None):
        return super().initRenderer(template,"home")

    def initBaseTemplateData(self,renderer):
        return renderer