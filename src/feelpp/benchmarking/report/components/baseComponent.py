import os

class BaseComponent:
    def __init__(self, id, display_name, description):
        self.id = id
        self.display_name = display_name
        self.description = description

        self.tree = {}

    def indexData(self,parent_id, self_tag_id):
        return dict(
            title = self.display_name,
            layout = "toolboxes",
            tags = f"catalog, toolbox, {self_tag_id}",
            description = self.description,
            parent_catalogs = parent_id,
            illustration = f"ROOT:{self.id}.jpg"
        )

    def initModules(self, base_dir, renderer, parent_id, self_tag_id):
        module_path = os.path.join(base_dir, self.id)

        if not os.path.exists(module_path):
            os.mkdir(module_path)

        renderer.render(
            os.path.join(module_path, "index.adoc"),
            self.indexData(parent_id, self_tag_id)
        )

    def printHierarchy(self):
        print(f"{self.display_name}")
        for k, vs in self.tree.items():
            print(f"\t{k.display_name}")
            for v,reports in vs.items():
                print(f"\t\t{v.display_name} : {len(reports)}")