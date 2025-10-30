from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.component.node import NodeComponent
from feelpp.benchmarking.dashboardRenderer.views.base import View, ViewFactory

import os

class NodeComponentRepository(Repository):
    """ Repository for Node Components. """
    def __init__(self,id, components:dict[str,dict],view:View) -> None:
        """
        Args:
            id (str): Unique identifier for the repository.
            components (dict[str,dict]): Dictionary containing component IDs and their metadata.
        """
        super().__init__(id)
        self.data: list[NodeComponent] = []
        self.view = view

        for component_id, node_template_info in components.items():
            self.add(NodeComponent(component_id,self,ViewFactory.create("node",node_template_info,component_id=component_id)))

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

    def upstreamView(self,
                    dataCb = lambda parent_id, component_id ,component_data : component_data.update({parent_id:component_id}),
                    leafCb = lambda leaves_info : [leaf_data.update({parent_id:leaf_id}) for (parent_id, leaf_id, leaf_data) in leaves_info] ):
        for node in self.data:
            node.upstreamView(parent_id=self.id,dataCb=dataCb,leafCb=leafCb)

        node_results = [node.view.template_data for node in self.data]
        combined = dataCb(f"repository-{self.id}",self.id, node_results)
        self.view.updateTemplateData(combined)