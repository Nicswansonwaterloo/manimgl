from __future__ import annotations

import re
from functools import lru_cache

from manimlib.utils.tex_to_symbol_count import TEX_TO_SYMBOL_COUNT


# These math alphabets form ligatures in the default TeX template. Text
# ligatures are normally disabled there, except in its sans-serif font.
LIGATURE_COMMANDS = {'operatorname', 'mathrm', 'mathbf', 'mathit', 'mathsf', 'textsf'}
FONT_COMMANDS = LIGATURE_COMMANDS | {
    'mathtt', 'mathnormal', 'mathbb', 'mathcal', 'mathscr', 'mathfrak', 'mathds',
    'boldsymbol', 'text', 'textrm', 'textnormal', 'textbf', 'textit', 'texttt',
    'textsl', 'textsc', 'emph', 'mbox',
}
PHANTOM_COMMANDS = {'phantom', 'hphantom', 'vphantom'}
DECORATION_COMMANDS = {
    'overline', 'underline', 'hat', 'bar', 'vec', 'dot', 'ddot', 'tilde',
    'widehat', 'widetilde', 'overbrace', 'underbrace', 'sqrt',
}
FRACTION_COMMANDS = {'frac', 'dfrac', 'tfrac'}
GROUP_COMMANDS = FONT_COMMANDS | PHANTOM_COMMANDS | DECORATION_COMMANDS | FRACTION_COMMANDS
COMMAND_PATTERN = r'\\(?:[a-zA-Z]+|[^\n])'


def tex_argument_end(tex: str, start: int) -> int:
    """Find a braced argument's end, including incomplete selection prefixes."""
    if start >= len(tex):
        return start
    if tex[start] != '{':
        match = re.match(COMMAND_PATTERN, tex[start:])
        return start + (match.end() if match else 1)
    depth = 0
    for match in re.finditer(r'\\.|[{}]', tex[start:]):
        if match.group() == '{':
            depth += 1
        elif match.group() == '}':
            depth -= 1
            if depth == 0:
                return start + match.end()
    return len(tex)


def split_tex_groups(tex: str):
    """Yield (command, argument, source) chunks for compound TeX groups.

    Other source is yielded with an empty command. Keep groups intact during
    matching because fonts affect counts and decorations reorder SVG paths.
    """
    pos = 0
    for match in re.finditer(COMMAND_PATTERN, tex):
        command = match.group()[1:]
        if match.start() < pos or command not in GROUP_COMMANDS:
            continue
        yield '', '', tex[pos:match.start()]
        start = match.end()
        while start < len(tex) and tex[start].isspace():
            start += 1
        if command == 'operatorname' and tex[start:start + 1] == '*':
            start += 1
            while start < len(tex) and tex[start].isspace():
                start += 1
        argument = ''
        if command == 'sqrt' and tex[start:start + 1] == '[':
            index_end = tex.find(']', start)
            if index_end == -1:
                index_end = len(tex)
            argument = tex[start + 1:index_end]
            start = min(index_end + 1, len(tex))
        end = start
        for _ in range(2 if command in FRACTION_COMMANDS else 1):
            while end < len(tex) and tex[end].isspace():
                end += 1
            start = end
            end = tex_argument_end(tex, start)
            argument += tex[start:end]
        yield command, argument, tex[match.start():end]
        pos = end
    yield '', '', tex[pos:]


@lru_cache
def num_tex_symbols(tex: str) -> int:
    """Estimate SVG glyphs for the default template (not a full TeX engine)."""
    return _num_tex_symbols(tex, False)


@lru_cache
def _num_tex_symbols(tex: str, ligatures: bool) -> int:
    tex = remove_tex_environments(tex)
    total = 0
    for command, argument, chunk in split_tex_groups(tex):
        if command in PHANTOM_COMMANDS:
            continue
        if command:
            if command in FONT_COMMANDS:
                total += _num_tex_symbols(argument, command in LIGATURE_COMMANDS)
            else:
                total += TEX_TO_SYMBOL_COUNT.get('\\' + command, 1)
                total += _num_tex_symbols(argument, ligatures)
            continue
        if ligatures:
            chunk = re.sub(
                COMMAND_PATTERN + r'|ffi|ffl|ff|fi|fl',
                lambda m: m.group() if m.group().startswith('\\') else '@',
                chunk,
            )
        pattern = r'\\sqrt\[[0-9]+\]|\\(?:left|right|middle)\s*\.|' + COMMAND_PATTERN
        pos = 0
        for match in re.finditer(pattern, chunk):
            total += sum(c not in '^{} \n\t_$\\&' for c in chunk[pos:match.start()])
            token = match.group()
            if token.startswith(r'\sqrt['):
                total += len(token) - 5
            elif re.fullmatch(r'\\(?:left|right|middle)\s*\.', token):
                pass  # Invisible delimiter
            else:
                total += TEX_TO_SYMBOL_COUNT.get(token, 1)
            pos = match.end()
        total += sum(c not in '^{} \n\t_$\\&' for c in chunk[pos:])
    return total


def get_tex_symbol_substrings(tex: str) -> list[str]:
    pattern = (
        r'\\sqrt\[[0-9]+\]|\\(?:left|right|middle)\s*\.|'
        + COMMAND_PATTERN + r'|[^\^{}\s_$\\&]'
    )
    return [
        symbol
        for command, _, chunk in split_tex_groups(remove_tex_environments(tex))
        for symbol in ([chunk] if command else re.findall(pattern, chunk))
    ]


def remove_tex_environments(tex: str) -> str:
    return re.sub(r'\\(begin|end)(\{\w+\*?\})?(\{\w+\})?(\[\w+\])?', '', tex)
