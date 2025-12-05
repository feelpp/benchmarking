import json, re

# https://stackoverflow.com/questions/29959191/how-to-parse-json-file-with-c-style-comments
class JSONWithCommentsDecoder(json.JSONDecoder):
    _COMMENT_RE = re.compile(
        r"""
        (//[^\n]*?$)              |   # // line comments
        (/\*.*?\*/)               |   # /* block comments */
        """,
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )

    _TRAILING_COMMA_RE = re.compile(
        r"""
        ,                      # a comma
        (?=\s*[\]}])           # followed only by spaces then } or ]
        """,
        re.VERBOSE
    )


    def __init__(self, **kw):
        super().__init__(**kw)

    def decode(self, s: str):
        no_comment = re.sub(self._COMMENT_RE, "", s)

        no_trailing_comma = self._TRAILING_COMMA_RE.sub("", no_comment)

        return super().decode(no_trailing_comma)