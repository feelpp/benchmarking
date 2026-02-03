import re
from feelpp.benchmarking.json_report.text.schemas.textSchema import Text
from jinja2 import Template

class Controller:
    def __init__(self, data, text:Text):
        self.text_config = text
        self.data = data

    @staticmethod
    def _asciidoc_to_latex_urls(text: str) -> str:
        pattern = re.compile(r'([(<]*)([a-zA-Z][a-zA-Z0-9+.-]*:\S+?)\[(.*?)\]([)>.,;!?:]*)')

        def repl(m):
            pre, url, label, post = m.groups()
            url = url.strip()
            label = label.strip()
            if label:
                replacement = r'\href{' + url + '}{' + label + '}'
            else:
                replacement = r'\url{' + url + '}'
            return pre + replacement + post

        return pattern.sub(repl, text)


    def formatText(self,text:str,format = "adoc"):
        if format == "adoc":
            pass
        elif format == "tex":
            # stem
            text = re.sub( r"stem:\[\s*(.*?)\s*\]", r"$\1$", text )

            #italics
            re.sub(r'(?<![A-Za-z0-9\$])_(\S(?:.*?\S)?)_(?![A-Za-z0-9\$])', r'\\textit{\1}', text)

            #bold
            text = re.sub(r"(?<![A-Za-z0-9])\*(.+?)\*(?![A-Za-z0-9])", r"\\textbf{\1}", text )

            #underline
            text = re.sub(r"r'\[\.underline\]#(.*?)#'", r"\\underline{\1}", text )

            #links
            text = self._asciidoc_to_latex_urls(text)

            #references
            text = re.sub(r"<<\s*([^\s,>]+)\s*(?:,\s*([^>]+))?\s*>>", lambda m : f"\\hyperlink{{{m.group(1)}}}{{{m.group(2)}}}" if m.group(2) else f"\\ref{{{m.group(1)}}}", text )


        else:
            raise NotImplementedError(f"Format not recognized in text controller: {format}")

        return text




    def generate(self, format="adoc"):
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

        return self.formatText(str(content),format)

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