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

    # ------------------------------------------------------------------
    # LaTeX formatting: escaping and conversions
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("text,expected", [
        (r"50% complete", r"50\% complete"),
        ("This is *bold* text", "This is \\textbf{bold} text"),
        ("*first* and *second*", "\\textbf{first} and \\textbf{second}"),
        ("stem:[x = \\frac{1}{2}]", "$x = \\frac{1}{2}$"),
        ("Math: stem:[ a^2 + b^2 ] here", "Math: $a^2 + b^2$ here"),
        ("https://example.com[Site]", "\\href{https://example.com}{Site}"),
        ("https://example.com[]", "\\url{https://example.com}"),
        ("<<section_id, Label>>", "\\hyperlink{section_id}{Label}"),
        ("<<equation_1>>", "\\ref{equation_1}"),
        ("*Bold* with stem:[x^2] and https://s.com[link]", 
         "\\textbf{Bold} with $x^2$ and \\href{https://s.com}{link}"),
    ])
    def test_latex_formatting_conversions(self, text, expected):
        """Test LaTeX format conversions from AsciiDoc syntax"""
        ctrl = Controller({}, Text(content=text))
        result = ctrl.generate(format="tex")
        assert result == expected

    def test_unknown_format_raises_error(self):
        """Unknown format should raise NotImplementedError"""
        ctrl = Controller({}, Text(content="test"))
        with pytest.raises(NotImplementedError):
            ctrl.generate(format="unknown")


