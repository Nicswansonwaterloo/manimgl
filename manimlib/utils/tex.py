from __future__ import annotations

import re
from functools import lru_cache

from manimlib.utils.tex_to_symbol_count import TEX_TO_SYMBOL_COUNT


def split_tex_operators(tex: str):
    """Yield (is_operator, text) chunks, retaining an operator's argument.

    Accept unfinished arguments as well, since substring selection counts
    prefixes of a TeX expression. Escaped braces do not affect nesting.
    """
    pos = 0
    pattern = r"\\operatorname(?![a-zA-Z])\s*\*?\s*"
    for match in re.finditer(pattern, tex):
        if match.start() < pos:
            continue
        yield False, tex[pos:match.start()]
        end = match.end()
        if end < len(tex) and tex[end] == "{":
            depth = 0
            for brace in re.finditer(r"\\.|[{}]", tex[end:]):
                if brace.group() == "{":
                    depth += 1
                elif brace.group() == "}":
                    depth -= 1
                    if depth == 0:
                        end += brace.end()
                        break
            else:
                end = len(tex)
        yield True, tex[match.start():end]
        pos = end
    yield False, tex[pos:]


@lru_cache
def num_tex_symbols(tex: str) -> int:
    tex = remove_tex_environments(tex)
    chunks = list(split_tex_operators(tex))
    if any(is_operator for is_operator, _ in chunks):
        total = 0
        for is_operator, chunk in chunks:
            if is_operator:
                chunk = re.sub(r"^\\operatorname\s*\*?\s*", "", chunk)
                # Roman operator letters form ligatures; math italic letters
                # outside the operator do not. Never rewrite command names.
                chunk = re.sub(
                    r"\\[a-zA-Z]+|ffi|ffl|ff|fi|fl",
                    lambda m: m.group() if m.group().startswith("\\") else "@",
                    chunk,
                )
            total += num_tex_symbols(chunk)
        return total
    commands_pattern = r"""
        (?P<sqrt>\\sqrt\[[0-9]+\])|    # Special sqrt with number
        (?P<escaped_brace>\\[{}])|      # Escaped braces
        (?P<cmd>\\[a-zA-Z!,-/:;<>]+)    # Regular commands
    """
    total = 0
    pos = 0
    for match in re.finditer(commands_pattern, tex, re.VERBOSE):
        # Count normal characters up to this command
        total += sum(1 for c in tex[pos:match.start()] if c not in "^{} \n\t_$\\&")

        if match.group("sqrt"):
            total += len(match.group()) - 5
        elif match.group("escaped_brace"):
            total += 1  # Count escaped brace as one symbol
        else:
            total += TEX_TO_SYMBOL_COUNT.get(match.group(), 1)
        pos = match.end()

    # Count remaining characters
    total += sum(1 for c in tex[pos:] if c not in "^{} \n\t_$\\&")
    return total


def remove_tex_environments(tex: str) -> str:
    # Handle \phantom{...} with any content
    tex = re.sub(r"\\phantom\{[^}]*\}", "", tex)
    # Handle other environment commands
    tex = re.sub(r"\\(begin|end)(\{\w+\})?(\{\w+\})?(\[\w+\])?", "", tex)
    return tex
