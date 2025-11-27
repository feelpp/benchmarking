import pytest
from pydantic import ValidationError

from feelpp.benchmarking.json_report.text.schemas.textSchema import Text

class TestTextSchema:

    @pytest.mark.parametrize(
        "value, expected_content, expected_mode",
        [
            ("hello world", "hello world", "static"),
            ("value is @{x}@", "value is @{x}@", "dynamic"),
        ]
    )
    def test_stringCoercion(self, value, expected_content, expected_mode):
        t = Text.model_validate(value)
        assert t.content == expected_content
        assert t.mode == expected_mode

    @pytest.mark.parametrize(
        "input_dict, expected_content, expected_mode",
        [
            ({"text": "hello"}, "hello", "static"),
            ({"content": "abc"}, "abc", "static"),
        ]
    )
    def test_dictCoercion(self, input_dict, expected_content, expected_mode):
        t = Text(**input_dict)
        assert t.content == expected_content
        assert t.mode == expected_mode

    @pytest.mark.parametrize(
        "content, placeholder_expr, expected_mode",
        [
            ("%%x%%", "%%([^%]+)%%", "dynamic"),
            ("%% x %%", "%%([^%]+)%%", "dynamic"), #Accepts whitespaces
            ("%{ Not Match for this }%", "__{[^%]+}__","static"),
            ("{{ Not Match for this either}}", "%{[^%]+}%","static")
        ]
    )
    def test_customPlaceholderExpr(self, content, placeholder_expr, expected_mode):
        t = Text(content=content, placeholder_expr=placeholder_expr)
        assert t.mode == expected_mode

    @pytest.mark.parametrize(
        "mode, content",
        [
            ("static", "value @{x}@"),
            ("dynamic", "hello world"),
        ]
    )
    def test_explicitModePreserved(self, mode, content):
        t = Text(mode=mode, content=content)
        assert t.mode == mode

    @pytest.mark.parametrize(
        "content, expected_mode",
        [
            ("value @{foo}@", "dynamic"),
            ("plain text", "static"),
            ("", "static"),
        ]
    )
    def test_defaultPlaceholderExpr(self, content, expected_mode):
        t = Text(content=content)
        assert t.mode == expected_mode

    @pytest.mark.parametrize(
        "data",
        [
            {"mode": "static"},  # missing content
            {"mode": "invalid", "content": "hi"},  # invalid mode
        ]
    )
    def test_validation_errors(self, data):
        with pytest.raises(ValidationError):
            Text(**data)

    def test_multiplePlaceholders(self):
        t = Text(content="a @{x}@ b @{y}@ c")
        assert t.mode == "dynamic"
