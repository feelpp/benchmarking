class TreeUtils:

    @staticmethod
    def treeToLists(tree, prefix=[]):
        tree_list = []
        for k, v in tree.items():
            new_prefix = prefix + [k]
            if isinstance(v, dict):
                tree_list.extend(TreeUtils.treeToLists(v, new_prefix))
            else:
                tree_list.append(new_prefix + [v])
        return tree_list


    @staticmethod
    def permuteTreeLevels(tree, permutation):
        """Permute the levels of an N-level nested dictionary tree"""
        branches = []

        def traverse(subtree, path):
            if isinstance(subtree, dict) and subtree:
                if all(isinstance(v, dict) for v in subtree.values()) or all(not isinstance(v, dict) for v in subtree.values()):
                    for key, child in subtree.items():
                        traverse(child, path + [key])
                else:
                    branches.append((path+["leaf"], subtree))
            else:
                branches.append((path, subtree))

        traverse(tree, [])

        N = len(permutation)
        for path, leaf in branches:
            if len(path) != N:
                raise ValueError(f"Branch {path} has {len(path)} levels but expected {N}.")

        new_branches = []
        for path, leaf in branches:
            new_path = [None] * N
            for new_level, old_level in enumerate(permutation):
                new_path[new_level] = path[old_level]
            new_branches.append((new_path, leaf))

        new_tree = {}
        for path, leaf in new_branches:
            current = new_tree
            for key in path[:-1]:
                if key not in current:
                    current[key] = {}

                elif not isinstance(current[key], dict):
                    raise ValueError(f"Conflict encountered at key '{key}' while rebuilding the tree.")
                current = current[key]

            current[path[-1]] = leaf

        return new_tree

    def mergeDicts(a, b):
        """Recursively merge dictionaries a and b."""
        result = a.copy()
        for key, value in b.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = TreeUtils.mergeDicts(result[key], value)
            else:
                result[key] = value
        return result