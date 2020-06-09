from typing import List
from dataclasses import dataclass
from ppdpy.expression_compiler import compile as compile_expression, \
    evaluate as evalexpr, \
    Node as ExpressionNode
from ppdpy.exceptions import DirectiveSyntaxError

LINEBREAK = '\n'

# Preprocessor Directive Sufix
PPD_PREFIX = '#'

_PPD_IF = ''
_PPD_ELIF = ''
_PPD_ELSE = ''
_PPD_ENDIF = ''


def set_directive_prefixes(prefix):
    global PPD_PREFIX, _PPD_IF, _PPD_ELIF, _PPD_ELSE, _PPD_ENDIF
    PPD_PREFIX = prefix

    _PPD_IF = PPD_PREFIX + 'if'
    _PPD_ELIF = PPD_PREFIX + 'elif'
    _PPD_ELSE = PPD_PREFIX + 'else'
    _PPD_ENDIF = PPD_PREFIX + 'endif'


set_directive_prefixes(PPD_PREFIX)


def compile(lines):
    iterlines = iter(lines)

    result = _parse(iterlines)
    return Template(result)


def _parse(lines):
    result, remainder = _parse_until(lines, tuple())
    return result


def _parse_until(lines, end_directives):
    result = []
    current_block = TextBlock()

    try:
        while True:
            line = next(lines).rstrip('\r\n')
            l = line.strip()

            if l.startswith(PPD_PREFIX):
                directive = _fetch_directive(l)

                if directive in end_directives:
                    result.append(current_block)
                    return result, l

                elif directive == _PPD_IF:
                    if current_block.text:
                        result.append(current_block)
                        current_block = TextBlock()

                    if_entries = list(_parse_if_entries(l, lines))
                    result.append(IfBlock(if_entries))

                else:
                    raise DirectiveSyntaxError('unexpected directive ' + directive)

            else:
                current_block.text += line + LINEBREAK

    except StopIteration:
        if end_directives:
            raise DirectiveSyntaxError('missing end directive')

        else:
            result.append(current_block)
            return result, None


def _parse_if_entries(last_line, lines):
    while True:
        if_expression = compile_expression(_fetch_expression(last_line))
        if_blocks, last_line = _parse_until(lines, (_PPD_ELIF, _PPD_ELSE, _PPD_ENDIF))
        yield IfEntry(if_expression, if_blocks)

        next_directive = _fetch_directive(last_line)
        if next_directive == _PPD_ENDIF:
            return

        elif next_directive == _PPD_ELSE:
            else_blocks, last_line = _parse_until(lines, (_PPD_ENDIF, ))
            yield ElseEntry(else_blocks)
            return

        elif next_directive != _PPD_ELIF:
            raise DirectiveSyntaxError()


def _fetch_directive(line):
    ls = line.strip().lower()
    try:
        return ls.split(' ')[0]

    except IndexError:
        if ls == _PPD_ELSE:
            return _PPD_ELSE

        elif ls == _PPD_ENDIF:
            return _PPD_ENDIF

        raise DirectiveSyntaxError()


def _fetch_expression(line):
    try:
        return line.split(' ', maxsplit=1)[1]

    except IndexError:
        raise DirectiveSyntaxError()


def render(template, symbols):
    """
    Renders a template using the given symbols
    """
    if not isinstance(template, Template):
        raise ValueError('template should be an instance of Template')

    if isinstance(symbols, dict):
        symbols = set(symbols.keys())

    else:
        symbols = set(symbols)

    return _render_sub_blocks(template, symbols)[:-len(LINEBREAK)]


def _render_sub_blocks(entry, symbols):
    return ''.join((_render_block(b, symbols) for b in entry.blocks))


def _render_block(block, symbols):
    def _render_conditional_block(ifblock, symbols):
        for ifentry in ifblock.if_entries:
            if isinstance(ifentry, IfEntry):
                if evalexpr(ifentry.expression, symbols):
                    return _render_sub_blocks(ifentry, symbols)

            elif isinstance(ifentry, ElseEntry):
                return _render_sub_blocks(ifentry, symbols)

            else:
                raise ValueError('unexpected conditional block type')

        # none of the blocks applied
        return ''

    if isinstance(block, TextBlock):
        return block.text

    elif isinstance(block, IfBlock):
        return _render_conditional_block(block, symbols)

    else:
        raise ValueError('unexpected block type')




class Block:
    pass


@dataclass
class Template:
    """
    A compiled text
    """
    blocks: List[Block]

    def render(self, symbols):
        """
        Shorthand for render(template, symbols)
        """
        return render(self, symbols)


@dataclass
class TextBlock(Block):
    """
    A block of plain text.
    """
    text: str = ''
    lines: int = 0


@dataclass
class IfBlock(Block):
    """
    A block of if conditional in the following pattern:
        #if a
        ...
        #elif b
        ...
        #else
        ...
        #endif
    """
    if_entries: List


@dataclass
class IfEntry:
    """
    A conditional entry composed of an expression and a text.
    When the expression evaluates to true, then the text is yielded,
    otherwise an empty string is yielded.
    """
    expression: ExpressionNode
    blocks: List[Block]


@dataclass
class ElseEntry:
    blocks: List[Block]
