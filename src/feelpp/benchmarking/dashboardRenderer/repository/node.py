from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.component.node import NodeComponent
from feelpp.benchmarking.dashboardRenderer.views.node import NodeComponentRepositoryView, NodeComponentView

import os

class NodeComponentRepository(Repository):
    """ Repository for Node Components. """
    def __init__(self,id, components:dict[str,dict],view:NodeComponentRepositoryView) -> None:
        """
        Args:
            id (str): Unique identifier for the repository.
            components (dict[str,dict]): Dictionary containing component IDs and their metadata.
        """
        super().__init__(id)
        self.data: list[NodeComponent] = []
        self.view = view

        for component_id, node_template_info in components.items():
            self.add(NodeComponent(component_id,self,NodeComponentView(component_id,node_template_info)))

    def printViews(self) -> None:
        """ Print the views of all components in the repository. """
        for component in self.data:
            print("\t",component.id)
            component.printViews()

    def render(self,base_dir:str) -> None:
        repository_dir = os.path.join(base_dir,self.id)

        self.view.render(repository_dir)

        for node in self.data:
            node.render(repository_dir,self.id)
