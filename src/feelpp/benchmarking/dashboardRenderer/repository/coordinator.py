from feelpp.benchmarking.dashboardRenderer.repository.registry import RepositoryRegistry
from feelpp.benchmarking.dashboardRenderer.component.node import NodeComponent
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import ComponentMap

class RepositoryCoordinator:
    """
    This class coordinates the interaction between different repositories.
    It is responsible for initializing and managing the views of components
    across different repositories.
    """
    def __init__(self, repository_registry: RepositoryRegistry) -> None:
        """
        Args:
            repository_registry (RepositoryRegistry): The repository registry containing all the repositories to be managed.
        """
        self.repository_registry = repository_registry

    def _processViewTree(self,view_order:list[str], subtree: dict, level_index:int = 0, unwrap_first:bool=False) -> dict:
        """
        Process the view tree to create a mapping of component IDs to their respective views.
        Args:
            view_order (list): The order of views to process.
            subtree (dict): The subtree to process.
            level_index (int): The current level index in the view order.
            unwrap_first (bool): If True, unwraps the first level of the tree.
        Returns:
            dict: A dictionary mapping component IDs to their respective views.
        """
        if level_index >= len(view_order) or not subtree:
            return {}

        current_repo = self.repository_registry.getRepository(view_order[level_index])
        grouped_subtree = {}
        for view_component_id, sub_tree in subtree.items():
            grouped_subtree.setdefault(view_order[level_index], {})[view_component_id] = sub_tree

        result = {}
        for component_type, components in grouped_subtree.items():
            level_result = {
                current_repo.get(comp_id): self._processViewTree(view_order,sub_tree, level_index + 1)
                for comp_id, sub_tree in components.items()
            }
            if unwrap_first:
                result.update(level_result)
            else:
                result.update({component_type:level_result})
        return result

    def initRepositoryViews(self, views:list, component_map: ComponentMap) -> None:
        """
        Initialize the views of components in the repositories based on the provided views and component map.
        Args:
            views (list): A list of views to initialize.
            component_map (ComponentMap): The component map containing the mapping of components to their respective repositories.
        """
        tree_order = component_map.component_order
        mapping = component_map.mapping
        for component_repository in self.repository_registry.node_repositories:
            component_views = views.get(component_repository.id,{})
            view_orders = TreeUtils.treeToLists({component_repository.id:component_views})
            for view_order in view_orders:
                view_perm = [tree_order.index(v) for v in view_order] + [len(view_order)]
                permuted_tree = TreeUtils.permuteTreeLevels(mapping,view_perm)
                for node_repository in self.repository_registry.node_repositories:
                    for component in node_repository.data:
                        component_subtree = permuted_tree.get(component.id, {})
                        component.views = TreeUtils.mergeDicts(component.views,{view_order[1]:self._processViewTree(view_order,component_subtree, 1, unwrap_first=True)})
                        self.addLeavesToNodeViews(component)


    def addLeavesToNodeViews(self,node:NodeComponent, views:dict = None,  path:list[str]=[]) -> None:
        """
        Update the views of the component with the provided leaves and views.
        Args:
            node (NodeComponent): The component to update.
            views (dict, optional): The views to update. Defaults to None.
            path (list[str], optional): The path to update. Defaults to [].
        """
        views = node.views if views is None else views

        if not isinstance(views,dict):
            return

        if views == {}:
            curr = node.views
            for key in path[:-1]:
                curr = curr.setdefault(key,{})
            curr[path[-1]] = list(
                filter(
                    lambda leaf: node.id in leaf.parent_ids and
                            all(p.id in leaf.parent_ids for p in path[1::2]),
                    self.repository_registry.leaf_repository
                )
            )
        else:
            for repo_id, component_views in views.items():
                for component, children_views in component_views.items():
                    self.addLeavesToNodeViews(
                        node,
                        views = children_views,
                        path = path + [repo_id,component]
                    )

    def setLeavesParents(self):
        for leaf in self.repository_registry.leaf_repository:
            for parent_id in leaf.parent_ids:
                leaf.addParent( self.repository_registry.getComponent(parent_id) )


    def patchTemplateInfo(self,patches:list[str],targets:str,prefix:str,save:bool):
        if not targets: #No target specified -> Select latest (by filename order).
            if len(patches) > 1:
                raise ValueError("When no patch reports are provided, plot configuration should be of length one")
            latest_leaf = max(self.repository_registry.leaf_repository, key = lambda report : report.id.split("-")[-1])
            print(f"Latest target: {latest_leaf.id}")
            latest_leaf.patchTemplateInfo(patches[0], prefix,save)
        else:
            for i, target in enumerate(targets):
                leaves_to_patch = self.repository_registry.leaf_repository
                for depth_i, component in enumerate(target):
                    if len(leaves_to_patch) == 0 :
                        raise ValueError(f"Component {component} not found")
                    if component == "all":
                        leaves_to_patch = leaves_to_patch
                    elif component == "latest":
                        leaves_to_patch = [max(leaves_to_patch, key = lambda leaf : leaf.id.split("-")[-1])]
                    else:
                        leaves_to_patch = list(filter(lambda leaf: leaf.id.split("-")[depth_i] == component, leaves_to_patch))

                for leaf_to_patch in leaves_to_patch:
                    patch = patches[i] if len(targets) == len(patches) else patches[0] if len(patches) == 1 else None
                    if not patch:
                        raise ValueError("Patches not must either be of length 1 or the same length as targets")
                    leaf_to_patch.patchTemplateInfo(patch, prefix,save)
