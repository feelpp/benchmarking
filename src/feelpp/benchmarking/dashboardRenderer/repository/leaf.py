from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import ComponentMap, LeafMetadata
from feelpp.benchmarking.dashboardRenderer.repository.leafLoader import LeafLoaderFactory

import os

class LeafComponentRepository(Repository):
    """ Repository for Leaf Components. """
    def __init__(self, id:str, component_mapping:ComponentMap) -> None:
        """
        Args:
            id (str): Unique identifier for the repository.
            component_mapping (ComponentMap): A hierarchy node component IDs and their children nodes and leaves.
        """
        super().__init__(id)
        for leaf_config, parent_ids in self.collectMetadata(component_mapping):
            LeafLoaderFactory.create(leaf_config).load(self, parent_ids)

    @staticmethod
    def collectMetadata(mapping:dict, path:list[str]=[]) -> list[tuple[LeafMetadata, list[str]]]:
        """ Recursively traverse the configuration mapping to collect leaf metadata.
        Args:
            mapping (dict): A nested dictionary representing the configuration.
            path (list[str]): Accumulated keys representing the current traversal path.
        Returns:
            list[tuple[LeafMetadata,list[str]]] : Each tuple consists of a LeafMetadata instance and its corresponding path.
        """

        if not isinstance(mapping, dict):
            return []

        if any(not isinstance(v, dict) for v in mapping.values()):
            return [( LeafMetadata(**mapping), path )]

        collected = []
        for k,v in mapping.items():
            collected += LeafComponentRepository.collectMetadata(v, path + [k])
        return collected

    def render(self,base_dir:str, parent_id:str = None) -> None:
        leaves_dir = os.path.join(base_dir,self.id)
        if not os.path.isdir(leaves_dir):
            os.mkdir(leaves_dir)
        for leaf in self.data:
            leaf.render(leaves_dir,parent_id)

