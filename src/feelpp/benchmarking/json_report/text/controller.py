import re
from feelpp.benchmarking.json_report.text.schemas.textSchema import Text
from jinja2 import Template

class Controller:
    def __init__(self, data, text:Text):
        self.text_config = text
        self.data = data

    def generate(self):
        if self.text_config.mode == "static":
            content = self.text_config.content

        elif self.text_config.mode == "dynamic":
            content = re.sub(
                self.text_config.placeholder_expr,
                self._resolvePlaceHolders,
                self.text_config.content
            )
            template = Template(content)
            content = template.render()

        else:
            content = self.text_config.content

        return content

    def _resolvePlaceHolders(self, match):
        expr = match.group(1)

        if "|" in expr:
            parts = [p.strip() for p in expr.split("|")]
            path_str = parts[0]
            ops = parts[1:]
        else:
            path_str = expr
            ops = []

        path = path_str.split(".")
        value = self.data
        if isinstance(value,dict):
            try:
                for key in path:
                    if isinstance(value, list):
                        key = int(key)
                    value = value[key]
            except (KeyError, IndexError, TypeError, ValueError):
                return match.group(0)

        for op in ops:
            if op == "length":
                value = len(value)
        return str(value)