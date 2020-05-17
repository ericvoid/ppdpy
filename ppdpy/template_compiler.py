from ppdpy.expression_compiler import compile as compile_expression
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
                current_block.add_text(line)

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


class Template:
    """
    A compiled text
    """
    def __init__(self, blocks=[]):
        self._blocks = blocks

    def render(self, symbols):
        if isinstance(symbols, dict):
            ss = set(symbols.keys())

        else:
            ss = set(symbols)

        return ''.join([block.apply(ss) for block in self._blocks])[:-len(LINEBREAK)]


class TextBlock:
    """
    A block of plain text.
    """
    def __init__(self):
        self.text = ''
        self.lines = 0

    def add_text(self, more):
        self.text += more + LINEBREAK
        # if self.lines == 0:
        #     self.text += more
        #     self.lines += 1

        # else:
        #     self.text += LINEBREAK + more
        #     self.lines += 1

    def eval(self, symbols):
        return True

    def apply(self, symbols):
        return self.text


class IfBlock:
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
    def __init__(self, if_entries):
        self._if_entries = if_entries

    def apply(self, symbols):
        for entry in self._if_entries:
            if entry.eval(symbols):
                return entry.apply(symbols)

        # none of the blocks applied
        return ''


class IfEntry:
    """
    A conditional entry composed of an expression and a text.
    When the expression evaluates to true, then the text is yielded,
    otherwise an empty string is yielded.
    """
    def __init__(self, expression, blocks):
        self._expression = expression
        self._blocks = blocks

    def eval(self, symbols):
        return self._expression.eval(symbols)

    def apply(self, symbols):
        return ''.join([block.apply(symbols) for block in self._blocks])


class ElseEntry:
    """
    """
    def __init__(self, blocks):
        self._blocks = blocks

    def eval(self, symbols):
        return True

    def apply(self, symbols):
        return ''.join([block.apply(symbols) for block in self._blocks])
