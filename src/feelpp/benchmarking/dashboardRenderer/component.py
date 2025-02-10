from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import ComponentMetadata

class Component:
    def __init__(self, id, component_metadata: ComponentMetadata):
        self.id = id
        self.display_name = component_metadata.display_name
        self.description = component_metadata.description

        self.views = {}

    def __repr__(self):
        return f"<{self.id}>"