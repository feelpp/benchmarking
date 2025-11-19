from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import ComponentMap, LeafMetadata,TemplateInfo
from feelpp.benchmarking.dashboardRenderer.repository.leafLoader import LeafLoaderFactory
from typing import Optional, List, Dict, Any, Tuple
import os

class LeafComponentRepository(Repository):
    """ Repository for Leaf Components.

    This specialized repository is responsible for traversing a structured configuration map,
    extracting metadata for all leaf components, merging default template information,
    and loading the actual LeafComponent instances into the repository's data storage.
    """
    def __init__( self, id:str, component_mapping:ComponentMap, default_template_info: Optional[TemplateInfo] = None ) -> None:
        """
        Args:
            id (str): Unique identifier for the repository.
            component_mapping (ComponentMap): A nested dictionary (ComponentMap) defining the hierarchy of component IDs and ultimately the metadata for the leaf components.
            default_template_info (Optional[TemplateInfo]): Default template configuration to be merged into each leaf's metadata. Defaults to None.
        """
        super().__init__( id )
        for leaf_config, parent_ids in self.collectMetadata( component_mapping ):
            if not leaf_config.template_info.template:
                leaf_config.template_info.template = default_template_info.template
            leaf_config.template_info.data += default_template_info.data
            LeafLoaderFactory.create( leaf_config ).load( self, parent_ids )

    @staticmethod
    def collectMetadata( mapping:Dict[str,Any], path:Optional[List[str]] = [] ) -> List[Tuple[LeafMetadata, List[str]]]:
        """
        Recursively traverses the configuration mapping to collect leaf metadata and the hierarchical path leading to it.
        A 'leaf' is identified when any of the values in the dictionary are not dictionaries themselves, meaning the dictionary can be unpacked into a LeafMetadata object.

        Args:
            mapping (Dict[str, Any]): A nested dictionary representing the configuration hierarchy (ComponentMap).
            path (List[str]): Accumulated keys (component IDs) representing the current traversal path to the current level. Defaults to an empty list.

        Returns:
            List[Tuple[LeafMetadata, List[str]]]: A list where each tuple consists of a **LeafMetadata** instance (the leaf configuration) and its corresponding **path** (parent IDs).
        """

        if not isinstance(mapping, dict):
            return []

        if any(not isinstance(v, dict) for v in mapping.values()):
            return [( LeafMetadata( **mapping ), path )]

        collected = []
        for k,v in mapping.items():
            collected += LeafComponentRepository.collectMetadata( v, path + [k] )
        return collected

    def render( self, base_dir:str ) -> None:
        """
        Renders all Leaf Components stored in the repository.

        Each leaf component is rendered into a subdirectory named after the repository's ID within the provided base directory.

        Args:
            base_dir (str): The base directory where the rendering output will be placed.
        """
        leaves_dir = os.path.join( base_dir, self.id )
        if not os.path.isdir( leaves_dir ):
            os.mkdir( leaves_dir )
        for leaf in self.data:
            leaf.render( leaves_dir )

