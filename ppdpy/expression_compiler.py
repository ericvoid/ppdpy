from ppdpy.nodes import *
from ppdpy.exceptions import ExpressionSyntaxError
from ppdpy.utility import listview

LP = '('
RP = ')'

TK_AND = 'and'
TK_OR = 'or'
TK_NOT = 'not'


def compile(x):
    return parse(list(lex(x)))


def lex(text:str):
    """
    Splits a text to a list of tokens.
    """
    token = ''
    for char in text:
        if char == ' ':
            if token:
                yield _clear_op(token)
                token = ''

            continue

        elif char == LP:
            if token:
                yield _clear_op(token)
                token = ''

            yield LP

        elif char == RP:
            if token:
                yield _clear_op(token)
                token = ''

            yield RP

        else:
            token += char

    if token:
        yield _clear_op(token)
        token = ''


def _clear_op(token):
    tl = token.lower()
    return tl if tl in (TK_AND, TK_OR, TK_NOT) else token


def parse(tokens):
    try:
        if len(tokens) == 0:
            raise ExpressionSyntaxError('empty expression')

        node, remainder = _parse_expr(listview(tokens))

        if remainder:
            raise ExpressionSyntaxError()

        return node

    except StopIteration:
        raise ExpressionSyntaxError


def _parse_expr(tokens):
    """
    Tries to parse a new expression, beginning with the left side of it.
    """
    head, tail = tokens.walk()

    if head == TK_NOT:
        # parses: not TOKEN
        return _parse_expr_not(tail)

    elif head == LP:
        # parses: (EXPRESSION)
        node, remainder = _parse_parens_contents(tokens)
        return _parse_cont(node, remainder)

    elif _is_id(head):
        # parses: ID
        node = _parse_id(head)
        return _parse_cont(node, tail)

    else:
        raise ExpressionSyntaxError('error parsing expression beginning')


def _parse_expr_not(tokens):
    head = tokens.head

    if _is_id(head):
        # parses: not ID
        node = Not(_parse_id(head))
        return _parse_cont(node, tokens.tail)

    elif head == LP:
        # parses: not (EXPRESSION)
        node, remainder = _parse_parens_contents(tokens)
        return _parse_cont(Not(node), remainder)

    else:
        raise ExpressionSyntaxError()


def _parse_cont(left, tokens):
    """
    Tries to parse an operator and the right side of the expression.
    """
    if len(tokens) == 0:
        # nothing left to parse
        return left, []

    head, tail = tokens.walk()

    if head == RP:
        # found a closing parens
        return left, tokens

    elif head == TK_OR:
        # parses: LEFT or RIGHT
        # does a late binding on "left or right" (low precedence)
        right, remainder = _parse_expr(tail)
        return Or(left, right), remainder

    elif head == TK_AND:
        # parses: LEFT and RIGHT
        return _parse_cont_and(left, tail)

    else:
        raise ExpressionSyntaxError()


def _parse_cont_and(left, tokens):
    # parses: LEFT and RIGHT
    # Does an early binding on "left and right" (high precedence)
    head, tail = tokens.walk()

    if _is_id(head):
        # parses: LEFT and ID
        right = _parse_id(head)
        node = And(left, right)
        return _parse_cont(node, tail)

    elif head == LP:
        # parses: LEFT and (EXPRESSION)
        right, remainder = _parse_parens_contents(tokens)
        node = And(left, right)
        return _parse_cont(node, remainder)

    elif head == TK_NOT:
        head2 = tail.head

        if _is_id(head2):
            # parses: LEFT and not ID
            right = Not(_parse_id(head2))
            node = And(left, right)
            return _parse_cont(node, tail.tail)

        elif head2 == LP:
            # parses: LEFT and not (EXPRESSION)
            right, remainder = _parse_parens_contents(tail)
            node = And(left, Not(right))
            return _parse_cont(node, remainder)

        else:
            raise ExpressionSyntaxError()

    else:
        raise ExpressionSyntaxError('unexpected token after and')


def _parse_parens_contents(tokens):
    head, tail = tokens.walk()

    if head != LP:
        raise ExpressionSyntaxError('left parens expected')

    node, remainder = _parse_expr(tail)
    if not remainder:
        raise ExpressionSyntaxError('right parens expected')

    elif remainder.head == RP:
        return node, remainder.tail

    else:
        raise ExpressionSyntaxError('right parens expected')



def _parse_id(token:str) -> Id:
    if not _is_id(token):
        raise ExpressionSyntaxError()

    else:
        return Id(token)


def _is_id(token:str) -> bool:
    assert isinstance(token, str)
    return token not in (LP, RP, TK_NOT, TK_AND, TK_OR)
