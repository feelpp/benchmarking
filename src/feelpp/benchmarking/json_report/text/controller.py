import re
from feelpp.benchmarking.json_report.text.schemas.textSchema import Text

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
        else:
            content = self.text_config.content

        return content

    def _resolvePlaceHolders(self, match):
        path = match.group(1).split(".")
        value = self.data
        try:
            for key in path:
                if isinstance(value, list):
                    key = int(key)
                value = value[key]
            return str(value)
        except (KeyError, IndexError, TypeError, ValueError):
            return match.group(0)
