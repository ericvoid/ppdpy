from typing import List, Tuple
from dataclasses import dataclass
from ppdpy.expression_compiler import compile as compile_expression, \
    evaluate as evaluate_expression, \
    Node as ExpressionNode, \
    TrueNode
from ppdpy.exceptions import PpdPyError, DirectiveSyntaxError

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

    result, remainder = _parse_until(iterlines, tuple())

    if remainder:
        raise PpdPyError('parse ended unexpectedly')

    return Template(result)

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
                    result.append(ConditionalBlock(if_entries))

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
        try:
            expression_string = last_line.split(' ', maxsplit=1)[1]

        except IndexError:
            raise DirectiveSyntaxError()

        if_expression = compile_expression(expression_string)
        if_blocks, last_line = _parse_until(lines, (_PPD_ELIF, _PPD_ELSE, _PPD_ENDIF))
        yield (if_expression, if_blocks)

        next_directive = _fetch_directive(last_line)
        if next_directive == _PPD_ENDIF:
            return

        elif next_directive == _PPD_ELSE:
            else_blocks, last_line = _parse_until(lines, (_PPD_ENDIF, ))
            yield (TrueNode(), else_blocks)
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

    def _render_block(block):
        if isinstance(block, TextBlock):
            return block.text

        elif isinstance(block, ConditionalBlock):
            for expression, inner_blocks in block.if_entries:
                if evaluate_expression(expression, symbols):
                    return _render_block_list(inner_blocks)

            # none of the blocks applied
            return ''

        else:
            raise ValueError('unexpected block type')

    def _render_block_list(blocks):
        return ''.join((_render_block(block) for block in blocks))

    return _render_block_list(template.blocks)[:-len(LINEBREAK)]


class TemplateBlock:
    pass


@dataclass
class Template:
    """
    A compiled text
    """
    blocks: List[TemplateBlock]

    def render(self, symbols):
        """
        Shorthand for render(template, symbols)
        """
        return render(self, symbols)


@dataclass
class TextBlock(TemplateBlock):
    """
    A block of plain text.
    """
    text: str = ''
    lines: int = 0


ConditionalEntry = Tuple[ExpressionNode, List[TemplateBlock]]


@dataclass
class ConditionalBlock(TemplateBlock):
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
    if_entries: List[ConditionalEntry]
