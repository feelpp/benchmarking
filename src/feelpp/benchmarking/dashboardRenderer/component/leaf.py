from feelpp.benchmarking.dashboardRenderer.component.base import GraphNode
from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.views.base import View
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateDataFile
import os,warnings,json
from typing import List, Union

class LeafComponent(GraphNode):
    """
    Class that represents a **leaf node** in a component graph structure.

    Leaf components are typically associated with specific items or data entries
    within a repository and are responsible for final rendering of that item.
    They cannot have children but can have multiple parents
    """
    def __init__( self, item_name:str, parent_repository:Repository, parent_ids:List[str], view:View ) -> None:
        """
        The ID is constructed using the hyphen-joined parent IDs and the item name:
        `<parent_id_1>-<parent_id_2>-...-<item_name>`.

        Args:
            item_name (str): The name or unique identifier of the item this leaf represents within the repository.
            parent_repository (Repository): The repository instance that contains objects of the same type
            parent_ids (List[str]): An ordered list of IDs representing the hierarchy of parent components leading to this leaf.
            view (View): The View object associated with this leaf for rendering.
        """
        super().__init__( f"{'-'.join([p for p in parent_ids])}-{item_name}", view )
        self.setRepository( parent_repository )

        self.item_name : str = item_name
        self.parent_ids : List[str] = parent_ids

    def clone( self ) -> None:
        """
        Leaf components are not intended to be cloned.

        Raises:
            RuntimeError: Always raises a RuntimeError, as cloning is disallowed.
        """
        raise RuntimeError("Leaf component cannot be cloned")

    def getPermParentIdsStr( self ) -> str:
        """
        Calculates and returns a comma-separated string of the hierarchical parent ID paths.
        Returns:
            str: A comma-separated string of parent ID paths (e.g., 'parentA-parentB,parentC').
        """
        branches = []
        for branch in self.getPathToRoot():
            branches.append( "-".join([b.id for b in branch[1:][::-1]]) )
        return ",".join( branches )

    def render( self, base_dir:str ) -> None:
        """
        Renders the leaf component's view in its dedicated subdirectory.

        Updates the view's template data with hierarchical path information
        and file relative paths before rendering the template.

        Args:
            base_dir (str): The base directory for all component output.
        """

        self.view.updateTemplateData( dict(
            parent_ids = self.getPermParentIdsStr()
        ) )
        leaf_dir = os.path.join( base_dir, self.id )

        self.view.updateTemplateData( dict(
            self_relpath = os.path.relpath( leaf_dir, os.path.join(base_dir,"..") ),
        ) )

        self.view.copyPartials( leaf_dir, os.path.join(base_dir,"..") )

        self.view.render( leaf_dir )

    def patchTemplateInfo( self, patch : Union[dict,TemplateDataFile], prefix:str, save:bool = False ) -> None:
        """
        Updates the view's template data with a patch and optionally saves the patch
        to a corresponding data file linked to the view.

        Args:
            patch (Union[dict,TemplateDataFile]): The data to be patched into the template data.
            prefix (str): The key under which the patch should be stored in the template data.
                          This key is also used to identify the TemplateDataFile to save to.
            save (bool): If True, the patch will be written back to the associated data file
                         (e.g., a JSON file) on the filesystem.
        """
        if save:
            template_data_files = [d for d in self.view.template_info.data if isinstance(d,TemplateDataFile) and d.prefix and d.prefix == prefix ]

            if len( template_data_files ) > 1:
                warnings.warn(f"More than one file having prefix {prefix} found. First occurence will be overwritten")

            filepath = None
            if len( template_data_files ) == 0:
                warnings.warn(f"No data files with {prefix} found in {self.id}. Saving this patch will not be possible.")
            else:
                filepath = template_data_files[0].filepath
                format = template_data_files[0].format

            if filepath:
                with open( os.path.join( self.view.template_data_dir, filepath ), "w" ) as f:
                    if format == "json":
                        json.dump( patch.model_dump(), f )
                    else:
                        f.write( patch )
        self.view.updateTemplateData( {prefix:patch} )