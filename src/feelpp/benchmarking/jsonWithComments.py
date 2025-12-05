import json, re

class JSONWithCommentsDecoder(json.JSONDecoder):
    _COMMENT_RE = re.compile(
        r"""
        ("(?:\\.|[^"\\])*") |       # JSON string (preserve)
        (//.*?$|/\*.*?\*/)\s*       # Single-line or multi-line comment (remove)
        """,
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )

    _TRAILING_COMMA_RE = re.compile( r""" ,(?=\s*[\]}])""",re.VERBOSE )


    def __init__(self, **kw):
        super().__init__(**kw)

    def replacer(self,match):
        return match.group(1) or ""

    def decode(self, s: str):
        no_comment = self._COMMENT_RE.sub(self.replacer, s)

        no_trailing_comma = self._TRAILING_COMMA_RE.sub("", no_comment)

        return super().decode(no_trailing_comma)