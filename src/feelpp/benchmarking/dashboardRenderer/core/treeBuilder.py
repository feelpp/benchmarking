from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema, TemplateInfo
from feelpp.benchmarking.dashboardRenderer.views.base import ViewFactory
from feelpp.benchmarking.dashboardRenderer.component.base import TreeNode,GraphNode
from feelpp.benchmarking.dashboardRenderer.component.leaf import LeafComponent
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.repository.leaf import LeafComponentRepository
import warnings
from typing import Dict, List

class ComponentTree(TreeNode):
    """
    Represents the complete hierarchical structure of the dashboard components.
    This class extends TreeNode to serve as the root of the entire dashboard,
    handling the organization of repositories, nodes, and leaves based on the provided DashboardSchema configuration.
    """
    def __init__( self, components_config:DashboardSchema ) -> None:
        """Args:
            components_config (DashboardSchema): The complete configuration schema
                                                 defining the dashboard structure, components, and mappings.
        """
        super().__init__( "dashboard_index", ViewFactory.create("home",components_config.dashboard_metadata) )
        self.levels = components_config.component_map.component_order

        self.repositories = self.createRepositories( components_config.repositories )
        self.leaf_repository = LeafComponentRepository( "leaves", components_config.component_map.mapping, components_config.template_defaults.leaves )

        self.buildTree( components_config )


    def createRepositories( self, repository_data: Dict[str,TemplateInfo] ) -> List[TreeNode]:
        """
        Creates repository nodes from the configuration data.
        Repositories are implemented as standard TreeNodes that will hold the branches of the component tree.

        Args:
            repository_data (Dict[str, TemplateInfo]): A dictionary mapping repository IDs to their TemplateInfo configuration.
        Returns:
            List[TreeNode]: A list of initialized TreeNode objects representing repositories.
        """
        return [
            TreeNode( repo_id, ViewFactory.create("node",repo_data,component_id=repo_id))
            for repo_id, repo_data in repository_data.items()
        ]

    def buildTree( self, components_config: DashboardSchema ) -> None:
        """
        Constructs the hierarchical component tree structure based on the mapping and component definitions.

        The process involves:
        1. Building the core component structure (non-leaf nodes).
        2. Attaching leaf components to their correct parent nodes.
        3. Permuting the component structure based on defined views.
        4. Finalizing the structure by linking view-based branches to the main repositories.

        Args:
            components_config (DashboardSchema): The complete configuration object.
        """
        mapping = components_config.component_map.mapping
        components = components_config.components
        max_depth = len(self.levels)

        repo_map = {r.id : r for r in self.repositories}

        def _buildSubtree( parent_node: TreeNode, subtree: dict, depth:int = 0 ):
            repository_id = self.levels[depth]

            if repository_id not in components: return

            repository_components = components[repository_id]
            for node_key, node_data in subtree.items():
                if depth >= max_depth:
                    continue

                if node_key not in repository_components:
                    continue

                child_node = TreeNode( node_key, ViewFactory.create( "node", repository_components[node_key], component_id=node_key ), parent_node )
                child_node.setRepository( repo_map.get(repository_id) )
                parent_node.addChild(child_node)

                if isinstance( node_data, dict ) and depth + 1 < max_depth:
                    _buildSubtree( child_node, node_data, depth + 1 )

        tmp_tree = TreeNode( "tmp", None )
        if max_depth > 0:
            _buildSubtree( tmp_tree, mapping )
        leaf:LeafComponent
        for leaf in self.leaf_repository:
            parent:TreeNode = tmp_tree
            for parent_id in leaf.parent_ids:
                parent = parent.get(parent_id)
            if not parent:
                warnings.warn(f"Could not find parent for leaf {leaf}")
                continue
            leaf.addParent(parent)

        view_orders = TreeUtils.dictTreeToLists( components_config.views )
        for view_order in view_orders:
            view_perm = [self.levels.index(v) for v in view_order if self.levels]
            view_tree: TreeNode = TreeUtils.permuteTree( tmp_tree, view_perm )
            parent_repository_id = view_order[0]

            repository = [repo for repo in self.repositories if repo.id == parent_repository_id]
            if not repository:
                raise ValueError(f"Repository {parent_repository_id} not defined")
            repository: TreeNode = repository[0]

            repository.setParent(self)
            for tree_child in view_tree.children:
                repository.addChild(tree_child)
                tree_child.parents.remove(view_tree)

        tmp_tree.unlink()
        del tmp_tree

        for leaf in self.leaf_repository:
            branches_to_rm: List[List[TreeNode]] = []
            for branch in leaf.getPathToRoot():
                if self not in branch:
                    branches_to_rm.append(branch)
            for b in branches_to_rm:
                for c in b[-1].children:
                    c.parents.remove(b[-1])
                b[-1].children.clear()

    def render( self, base_path:str ) -> None:
        """
        Renders the entire component tree structure to disk.
        It renders all repository and node pages (via the base class render) and then delegates the rendering of all leaf components to the LeafComponentRepository.

        Args:
            base_path (str): The root directory where the dashboard will be generated.
        """
        super().render(base_path,None,renderLeaves=False)
        self.leaf_repository.render(base_path)

    def patchTemplateInfo( self, patches:list[str], targets:str, prefix:str, save:bool = False ):
        """
        Applies template patches to specific leaf components based on the given target criteria.

        Args:
            patches (List[str]): List of patch file paths (JSON files) to apply to the template data.
            targets (List[str]): List of component ID paths (e.g., ["system_id", "test_id", "latest"]) that define which leaves to patch.
            prefix (str): The prefix key under which the patch data should be stored in the template data.
            save (bool): If True, the modified template info is saved back to disk.
        Raises:
            ValueError: If patch and target list lengths are inconsistent or components are not found.
        """
        if not targets: #No target specified -> Select latest (by filename order).
            if len(patches) > 1:
                raise ValueError("When no patch reports are provided, plot configuration should be of length one")
            latest_leaf:LeafComponent = max(self.leaf_repository, key = lambda report : report.id.split("-")[-1])
            print(f"Latest target: {latest_leaf.id}")
            latest_leaf.patchTemplateInfo(patches[0], prefix,save)
        else:
            for i, target in enumerate(targets):
                leaves_to_patch:LeafComponentRepository  = self.leaf_repository
                for depth_i, component in enumerate(target):
                    if len(leaves_to_patch) == 0 :
                        raise ValueError(f"Component {component} not found")
                    if component == "all":
                        leaves_to_patch = leaves_to_patch
                    elif component == "latest":
                        leaves_to_patch = [max( leaves_to_patch, key = lambda leaf : leaf.id.split("-")[-1] )]
                    else:
                        leaves_to_patch = list(filter(lambda leaf: leaf.id.split("-")[depth_i] == component, leaves_to_patch))

                for leaf_to_patch in leaves_to_patch:
                    leaf_to_patch:LeafComponent
                    patch = patches[i] if len(targets) == len(patches) else patches[0] if len(patches) == 1 else None
                    if not patch:
                        raise ValueError("Patches not must either be of length 1 or the same length as targets")
                    leaf_to_patch.patchTemplateInfo( patch, prefix, save )
