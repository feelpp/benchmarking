import pytest
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import ComponentMetadata
from feelpp.benchmarking.dashboardRenderer.repository import ComponentRepository
from feelpp.benchmarking.dashboardRenderer.component import Component
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils

class TestComponentRepository:

    @staticmethod
    def checkForDuplicates(list):
        assert len(list) == len(set(list)), "list has duplicate values"

    def test_uniqueness(self):
        components_config = {
            "a": ComponentMetadata(display_name = "A"),
            "b": ComponentMetadata(display_name = "B"),
            "c": ComponentMetadata(display_name = "C"),
            "a": ComponentMetadata(display_name = "A"),
        }
        component_repository = ComponentRepository("test",components_config)
        self.checkForDuplicates(component_repository.data)
        assert len([c for c in component_repository.data if c.id == "a"]) == 1

        component_repository.add(Component(id = "b",component_metadata=ComponentMetadata(display_name="Other")))
        self.checkForDuplicates(component_repository.data)
        assert len([c for c in component_repository.data if c.id == "b"]) == 1


    def test_initViews(self):
        """Test the initViews method with different view order permutations."""

        # --- Create Components in each repository ---
        components_config_1 = {"A1": ComponentMetadata(display_name="A1"), "A2": ComponentMetadata(display_name="A2")}
        components_config_2 = {"B1": ComponentMetadata(display_name="B1"), "B2": ComponentMetadata(display_name="B2")}
        components_config_3 = {"C1": ComponentMetadata(display_name="C1"), "C2": ComponentMetadata(display_name="C2")}
        components_config_4 = {"D1": ComponentMetadata(display_name="D1"), "D2": ComponentMetadata(display_name="D2")}

        # --- Create Repositories ---
        repo1 = ComponentRepository("Repo1", components_config_1)
        repo2 = ComponentRepository("Repo2", components_config_2)
        repo3 = ComponentRepository("Repo3", components_config_3)
        repo4 = ComponentRepository("Repo4", components_config_4)

        # Get the actual components from repositories
        component_A1 = repo1.get("A1")
        component_A2 = repo1.get("A2")
        component_B1 = repo2.get("B1")
        component_B2 = repo2.get("B2")
        component_C1 = repo3.get("C1")
        component_C2 = repo3.get("C2")
        component_D1 = repo4.get("D1")
        component_D2 = repo4.get("D2")

        repositories = [repo1, repo2, repo3, repo4]
        view_order = ["Repo1", "Repo2", "Repo3", "Repo4"]
        # --- Define a Hierarchical Tree ---
        tree = {
            "A1": {
                "B1": {
                    "C1": {
                        "D1": {}
                    },
                    "C2": {
                        "D2": {}
                    }
                },
                "B2": {
                    "C1": {
                        "D2": {}
                    }
                }
            },
            "A2": {
                "B1": {
                    "C2": {
                        "D1": {}
                    }
                }
            }
        }

        # --- Run initViews on repo1 ---
        repo1.initViews(view_order, tree, repositories)

        # Ensure view key exists in components
        assert view_order[1] in component_A1.views
        assert view_order[1] in component_A2.views

        # Expected structure after `initViews`
        expected_structure_A1 = {
            component_B1: {
                component_C1: {component_D1: {}},
                component_C2: {component_D2: {}}
            },
            component_B2: {
                component_C1: {component_D2: {}}
            }
        }

        expected_structure_A2 = {
            component_B1: {
                component_C2: {component_D1: {}}
            }
        }

        assert component_A1.views[view_order[1]] == expected_structure_A1, (
            f"Expected {expected_structure_A1}, but got {component_A1.views[view_order[1]]}"
        )

        assert component_A2.views[view_order[1]] == expected_structure_A2, (
            f"Expected {expected_structure_A2}, but got {component_A2.views[view_order[1]]}"
        )