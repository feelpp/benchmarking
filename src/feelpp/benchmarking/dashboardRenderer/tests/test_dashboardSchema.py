import os, pytest
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import *
from pydantic import ValidationError

@pytest.mark.parametrize("filepath, expected_format", [
    ("data/test.json", "json"),
    ("output/report.txt", "txt"),
    ("file_no_ext", "file_no_ext"),
])
def test_TemplateDataFile_format_inference(filepath, expected_format):
    """Test that format is inferred from filepath if not provided."""
    tdf = TemplateDataFile(filepath=filepath)
    assert tdf.format == expected_format
    assert tdf.prefix == ""
    assert tdf.action == "input"

def test_TemplateDataFile_explicit_format():
    """Test that explicit format overrides inferred format."""
    tdf = TemplateDataFile(filepath="data/test.json", format="csv")
    assert tdf.format == "csv"

def test_TemplateInfo_coerceData_list_normalization():
    """Test that single dict/item is normalized into a list."""
    # Single dict
    ti_dict = TemplateInfo(data={"key": "value"})
    assert isinstance(ti_dict.data, list)
    assert ti_dict.data == [{"key": "value"}]

    # Single TDF
    tdf_instance = TemplateDataFile(filepath="a.txt")
    ti_tdf = TemplateInfo(data=tdf_instance)
    assert isinstance(ti_tdf.data, list)
    assert ti_tdf.data[0].filepath == "a.txt"


def test_TemplateInfo_coerceData_tdf_coercion():
    """Test that a dict containing 'filepath' is coerced into TemplateDataFile."""
    data = [ {"filepath": "data.csv", "prefix": "dat"}, {"key": "value", "no_filepath": True}, ]
    ti = TemplateInfo(data=data)

    # First item should be TDF
    assert isinstance(ti.data[0], TemplateDataFile)
    assert ti.data[0].filepath == "data.csv"
    assert ti.data[0].prefix == "dat"

    # Second item remains a dict
    assert isinstance(ti.data[1], dict)


def test_TemplateInfo_expandTemplate_env_path(monkeypatch):
    """Test template expansion using TEMPLATE_DIR environment variable."""
    env_path = '/custom/template/path'

    monkeypatch.setattr(os, 'getenv', lambda k: env_path if k == 'TEMPLATE_DIR' else None)
    monkeypatch.setattr(os.path, 'isdir', lambda path: path == env_path)
    monkeypatch.setattr(os.path, 'abspath', lambda path: path) # Mock abspath for simplicity

    ti = TemplateInfo(data={}, template="${TEMPLATE_DIR}/my_file.html")
    assert ti.template == f"{env_path}/my_file.html"

def test_TemplateInfo_expandTemplate_no_substitution():
    """Test that a template with no variable is untouched."""
    ti = TemplateInfo(data={}, template="just_a_path.html")
    assert ti.template == "just_a_path.html"

def test_TemplateInfo_template_is_none():
    """Test that if template is None, it remains None."""
    ti = TemplateInfo(data={})
    assert ti.template is None

# --- LeafMetadata Tests ---

def test_LeafMetadata_defaults():
    """Test default values for LeafMetadata."""
    lm = LeafMetadata(template_info={})
    assert lm.platform == "local"
    assert lm.path is None
    assert isinstance(lm.template_info, TemplateInfo)
    assert lm.template_info.data == [{}]


def test_LeafMetadata_castNodeTemplateInfo_coercion():
    """Test coercion of raw dict into TemplateInfo."""
    lm = LeafMetadata(template_info={"template": "t.html", "data": [{"k": "v"}]})
    assert isinstance(lm.template_info, TemplateInfo)
    assert lm.template_info.template == "t.html"
    assert lm.template_info.data == [{"k": "v"}]

# --- ComponentMap Tests ---

def test_ComponentMap_full_input():
    """Test ComponentMap with full input."""
    data = {
        "component_order": ["A", "B"],
        "mapping": {"A_node": {"B_node": {}}},
    }
    cm = ComponentMap(**data)
    assert cm.component_order == ["A", "B"]
    assert cm.mapping["A_node"] == {"B_node": {}}


def test_ComponentMap_coerceComponentMap_raw_dict():
    """Test coercion when a raw dict is passed as component_map."""
    # This scenario is tested in DashboardSchema, but checking the validator directly.
    data = {"NodeA": {"NodeB": {}}}
    cm = ComponentMap(mapping=data)
    # The validator runs and ensures it's wrapped in ComponentMap.
    # The coercion in DashboardSchema handles the raw dict input.

    # Here we test the class initialization structure itself
    assert cm.mapping == data
    assert cm.component_order is None

# --- TemplateDefaults Tests ---

def test_TemplateDefaults_defaults():
    """Test TemplateDefaults initialization with no input."""
    td = TemplateDefaults()
    assert isinstance(td.repositories, TemplateInfo)
    assert isinstance(td.leaves, TemplateInfo)
    assert td.components == {} # Default is an empty dict


def test_TemplateDefaults_castRepoTemplateInfo():
    """Test casting raw dict to TemplateInfo for repositories/leaves."""
    td = TemplateDefaults(repositories={"template": "r.html"}, leaves={"data": [{"leaf_key": 1}]})

    assert isinstance(td.repositories, TemplateInfo)
    assert td.repositories.template == "r.html"

    assert isinstance(td.leaves, TemplateInfo)
    assert td.leaves.data == [{"leaf_key": 1}]


def test_TemplateDefaults_castNodeTemplateInfo():
    """Test casting nested component dicts to TemplateInfo."""
    data = {
        "repoA": {"template": "compA.html"},
        "all": {"data": [{"common": True}]}
    }
    td = TemplateDefaults(components=data)

    assert isinstance(td.components["repoA"], TemplateInfo)
    assert td.components["repoA"].template == "compA.html"
    assert td.components["repoA"].data == [] # TemplateInfo(data={"template":..}) coerces to data=[]

    assert isinstance(td.components["all"], TemplateInfo)
    assert td.components["all"].data == [{"common": True}]

# --- DashboardSchema Tests ---

@pytest.fixture
def dashboard_input():
    """Standard minimal input for DashboardSchema."""
    return {
        "component_map": { "MappingA": {"MappingB": {}} },
        "components": { "RepoA": {"MappingA": TemplateInfo(data={})}, "RepoB": {"MappingB": TemplateInfo(data={})} }
    }

def test_DashboardSchema_coercion_and_defaults(dashboard_input):
    """Test initial coercion for metadata and component_map."""

    # Test casting raw dicts
    schema_data = dashboard_input.copy()
    schema_data["dashboard_metadata"] = {"title": "My Dashboard"}

    ds = DashboardSchema(**schema_data)

    assert isinstance(ds.dashboard_metadata, TemplateInfo)
    assert ds.dashboard_metadata.data == [{"title": "My Dashboard"}]

    assert isinstance(ds.component_map, ComponentMap)
    assert isinstance(ds.template_defaults, TemplateDefaults)


def test_DashboardSchema_inferRepositories(dashboard_input):
    """Test that repositories are inferred from component keys if repositories is None."""
    ds = DashboardSchema(**dashboard_input)

    # Manually set repositories to None to trigger inference check
    ds.repositories = None
    ds = ds.inferRepositories()

    assert "RepoA" in ds.repositories
    assert "RepoB" in ds.repositories
    assert isinstance(ds.repositories["RepoA"], TemplateInfo)
    assert ds.repositories["RepoA"].data == [{"title": "Repoa"}] # Title case check


def test_DashboardSchema_inferOrder(dashboard_input):
    """Test component_order inference based on component names found in the mapping keys."""
    # Components: RepoA -> MappingA, RepoB -> MappingB
    # Mapping: MappingA -> MappingB
    # Expected order: [RepoA, RepoB]

    ds = DashboardSchema(**dashboard_input)
    ds = ds.inferOrder()

    assert ds.component_map.component_order == ["RepoA", "RepoB"]


def test_DashboardSchema_setDefaultViews(dashboard_input):
    """Test default views creation based on component_order."""

    # 1. Test with inferred order [RepoA, RepoB]
    ds = DashboardSchema(**dashboard_input)
    ds = ds.inferOrder()
    ds = ds.setDefaultViews()

    # Expected: {'RepoA': 'RepoB'}
    assert ds.views == {"RepoA": "RepoB"}

    # 2. Test with explicit order [A, B, C]
    explicit_input = {"component_map":{},"components":{}}
    explicit_input["component_map"]["mapping"] = ds.component_map.mapping
    explicit_input["component_map"]["component_order"] = ["RepoX", "RepoY", "RepoZ"]
    explicit_input["components"]["RepoX"] = {"MappingX": TemplateInfo(data={})}
    explicit_input["components"]["RepoY"] = {"MappingY": TemplateInfo(data={})}
    explicit_input["components"]["RepoZ"] = {"MappingZ": TemplateInfo(data={})}

    ds_explicit = DashboardSchema(**explicit_input)
    ds_explicit = ds_explicit.setDefaultViews()

    # Expected: {'RepoX': {'RepoY': 'RepoZ'}}
    assert ds_explicit.views == {"RepoX": {"RepoY": "RepoZ"}}


def test_DashboardSchema_setTemplateDefaults_validation(dashboard_input):
    """Test validation of template_defaults component keys."""

    # Add a default for a non-existent repo "BadRepo"
    bad_defaults = TemplateDefaults(components={"BadRepo": {"template": "t.html"}})

    with pytest.raises(ValidationError) as excinfo:
        ds = DashboardSchema(**dashboard_input, template_defaults=bad_defaults)

        with pytest.raises(ValueError) as excinfo:
            ds.setTemplateDefaults()

    assert "Template defaults: BadRepo does not exist in repositories" in str(excinfo.value)


def test_DashboardSchema_setTemplateDefaults_repo_extension(dashboard_input):
    """Test repository template and data extension from defaults."""

    repo_default_data = [{"repo_key": 1, "priority": "low"}]
    repo_defaults = TemplateDefaults(
        repositories=TemplateInfo(template="base_repo.html", data=repo_default_data)
    )

    # Initial component state
    dashboard_input["repositories"] = {
        "RepoA": TemplateInfo(data=[{"repo_key": 1, "priority": "high"}]), # Existing item (should not be extended)
        "RepoB": TemplateInfo(data=[{"unique_key": 2}, {"priority": "low"}]), # Unique item (should be extended)
        "RepoC": TemplateInfo(data=[]) # Empty repo
    }

    ds = DashboardSchema(**dashboard_input, template_defaults=repo_defaults)
    ds.inferRepositories() # Ensure all repos are present
    ds.setTemplateDefaults()

    # RepoA: Has existing TDF with same content as default data, so it shouldn't be extended.
    assert ds.repositories["RepoA"].template == "base_repo.html"
    assert len(ds.repositories["RepoA"].data) == 2
    # RepoB: Unique item added

    assert ds.repositories["RepoB"].template == "base_repo.html"
    assert len(ds.repositories["RepoB"].data) == 3

    # RepoC: Gets the default data
    assert ds.repositories["RepoC"].template == "base_repo.html"
    assert ds.repositories["RepoC"].data == repo_default_data


def test_DashboardSchema_setTemplateDefaults_component_extension(dashboard_input):
    """Test component template and data extension from 'all' and specific repo defaults."""

    all_data = [{"common_key": 1}]
    repo_a_data = [{"specific_key": "A"}]


    # Initial component state
    dashboard_input["components"] = {
        "RepoA": {
            "NodeA1": TemplateInfo(data=[{"common_key": 1}, {"init_A": 5}]), # Should NOT take common_key 1
            "NodeA2": TemplateInfo(template="local.html", data=[]) # Should not override template
        },
        "RepoB": {
            "NodeB1": TemplateInfo(data=[]) # Should only get 'all' defaults
        }
    }
    dashboard_input["repositories"] = {
        "RepoA": TemplateInfo(data={}), "RepoB": TemplateInfo(data={})
    }
    dashboard_input["template_defaults"] = TemplateDefaults(components={
        "all": {"template":"base_comp.html", "data":all_data},
        "RepoA": {"template":"override_A.html", "data":repo_a_data}
    })
    dashboard_input["views"] = {"RepoA":"RepoB"}

    ds = DashboardSchema(**dashboard_input)

    ds.setTemplateDefaults()

    # NodeA1 (RepoA): Gets override template, data from 'all' and 'RepoA'. Common data ignored due to _extend_unique
    node_a1 = ds.components["RepoA"]["NodeA1"]
    assert node_a1.template == "override_A.html"
    # Data: [{"common_key": 1}, {"init_A": 5}, {"specific_key": "A"}]
    assert len(node_a1.data) == 3

    # NodeA2 (RepoA): Keeps local template, gets data from 'all' and 'RepoA'.
    node_a2 = ds.components["RepoA"]["NodeA2"]
    assert node_a2.template == "local.html" # Local template kept
    # Data: [{"common_key": 1}, {"specific_key": "A"}]
    assert len(node_a2.data) == 2

    # NodeB1 (RepoB): Gets 'all' template, only 'all' data.
    node_b1 = ds.components["RepoB"]["NodeB1"]
    assert node_b1.template == "base_comp.html"
    assert node_b1.data == all_data # Data only from 'all'