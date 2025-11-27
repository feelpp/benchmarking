import pytest
from jinja2 import Template
from feelpp.benchmarking.json_report.text.schemas.textSchema import Text
from feelpp.benchmarking.json_report.text.controller import Controller

class TestController:

    # ------------------------------------------------------------------
    # Static mode
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("content, data",
        [
            ("Hello world", {}),
            ("No placeholders here", {"x": 1}),
        ],
    )
    def test_static_mode_returns_content_as_is(self, content, data):
        text = Text(content=content, mode="static")
        ctrl = Controller(data, text)
        result = ctrl.generate()
        assert result == content

    # ------------------------------------------------------------------
    # Dynamic mode: simple replacement
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("content, data, expected",
        [
            ("Value: @{x}@", {"x": 42}, "Value: 42"),
            ("Nested: @{user.name}@", {"user": {"name": "Alice"}}, "Nested: Alice"),
            ("List: @{items.1}@", {"items": [10, 20, 30]}, "List: 20"),
        ],
    )
    def test_dynamic_mode_simple_placeholders(self, content, data, expected):
        text = Text(content=content, mode="dynamic")
        ctrl = Controller(data, text)
        result = ctrl.generate()
        assert result == expected

    # ------------------------------------------------------------------
    # Dynamic mode: missing keys fallback
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("content, data, expected",
        [
            ("Missing: @{missing_key}@", {}, "Missing: @{missing_key}@"),
            ("Deep missing: @{user.age}@", {"user": {"name": "Bob"}}, "Deep missing: @{user.age}@"),
            ("List missing: @{items.5}@", {"items": [1, 2]}, "List missing: @{items.5}@"),
        ],
    )
    def test_dynamic_mode_missing_keys_fallback(self, content, data, expected):
        text = Text(content=content, mode="dynamic")
        ctrl = Controller(data, text)
        result = ctrl.generate()
        assert result == expected

    # ------------------------------------------------------------------
    # Dynamic mode: operations
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("content, data, expected",
        [
            ("Length: @{items | length}@", {"items": [1, 2, 3]}, "Length: 3"),
            ("Length empty: @{empty | length}@", {"empty": []}, "Length empty: 0"),
        ],
    )
    def test_dynamic_mode_operations(self, content, data, expected):
        text = Text(content=content, mode="dynamic")
        ctrl = Controller(data, text)
        result = ctrl.generate()
        assert result == expected

    # ------------------------------------------------------------------
    # Dynamic mode: multiple placeholders
    # ------------------------------------------------------------------
    def test_dynamic_mode_multiple_placeholders(self):
        data = {"x": 1, "y": 2}
        content = "Sum: @{x}@ + @{y}@"
        text = Text(content=content, mode="dynamic")
        ctrl = Controller(data, text)
        result = ctrl.generate()
        assert result == "Sum: 1 + 2"

    # ------------------------------------------------------------------
    # Edge case: placeholder_expr custom
    # ------------------------------------------------------------------
    def test_dynamic_mode_custom_placeholder_expr(self):
        content = "Custom: %%x%%"
        data = {"x": "ok"}
        text = Text(content=content, mode="dynamic", placeholder_expr=r"%%([^%]+)%%")
        ctrl = Controller(data, text)
        result = ctrl.generate()
        assert result == "Custom: ok"

    # ------------------------------------------------------------------
    # Dynamic mode: invalid operation ignored
    # ------------------------------------------------------------------
    def test_dynamic_mode_invalid_operation_ignored(self):
        content = "Value: @{x | unknown}@"
        data = {"x": "test"}
        text = Text(content=content, mode="dynamic")
        ctrl = Controller(data, text)
        result = ctrl.generate()
        # unknown op ignored, value replaced normally
        assert result == "Value: test"
