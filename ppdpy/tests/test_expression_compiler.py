from unittest import TestCase

from ppdpy.expression_compiler import lex, compile, Id, Not, And, Or, \
    evaluate as evalexpr
from ppdpy.exceptions import ExpressionSyntaxError


class TestLex(TestCase):
    def test_ids(self):
        self.assertEqual(list(lex('foo')), ['foo'])
        self.assertEqual(list(lex('foo bar')), ['foo', 'bar'])
        self.assertEqual(list(lex('foo   bar')), ['foo', 'bar'])
        self.assertEqual(list(lex('  foo bar')), ['foo', 'bar'])
        self.assertEqual(list(lex('foo bar  ')), ['foo', 'bar'])
        self.assertEqual(list(lex('   foo   bar   ')), ['foo', 'bar'])

    def test_parens(self):
        self.assertEqual(list(lex('()')), ['(', ')'])
        self.assertEqual(list(lex(' ()')), ['(', ')'])
        self.assertEqual(list(lex('( )')), ['(', ')'])
        self.assertEqual(list(lex('() ')), ['(', ')'])
        self.assertEqual(list(lex(' ( ) ')), ['(', ')'])
        self.assertEqual(list(lex('  (  )  ')), ['(', ')'])
        self.assertEqual(list(lex('   (   )   ')), ['(', ')'])

        self.assertEqual(list(lex('(())')), ['(', '(', ')', ')'])
        self.assertEqual(list(lex('(  ())')), ['(', '(', ')', ')'])
        self.assertEqual(list(lex('((  ))')), ['(', '(', ')', ')'])
        self.assertEqual(list(lex('(())  ')), ['(', '(', ')', ')'])

        self.assertEqual(list(lex(')()(')), [')', '(', ')', '('])

    def test_expressions(self):
        self.assertEqual(list(lex('a and b')), ['a', 'and', 'b'])
        self.assertEqual(list(lex('a and b or c')), ['a', 'and', 'b', 'or', 'c'])

        self.assertEqual(list(lex('(a)')), ['(', 'a', ')'])
        self.assertEqual(list(lex('(a and b) or c')), ['(', 'a', 'and', 'b', ')', 'or', 'c'])
        self.assertEqual(list(lex('(a and b)or c')), ['(', 'a', 'and', 'b', ')', 'or', 'c'])

        self.assertEqual(list(lex('not (a and b) or c')), ['not', '(', 'a', 'and', 'b', ')', 'or', 'c'])
        self.assertEqual(list(lex('not(a and b)or c')), ['not', '(', 'a', 'and', 'b', ')', 'or', 'c'])

        self.assertEqual(list(lex('a and (b or c)')), ['a', 'and', '(', 'b', 'or', 'c', ')'])
        self.assertEqual(list(lex('a and(b or c)')), ['a', 'and', '(', 'b', 'or', 'c', ')'])
        self.assertEqual(list(lex('a and not (b or c)')), ['a', 'and', 'not', '(', 'b', 'or', 'c', ')'])
        self.assertEqual(list(lex('a and not(b or c)')), ['a', 'and', 'not', '(', 'b', 'or', 'c', ')'])
        self.assertEqual(list(lex('  a    and  (b   or  c) ')), ['a', 'and', '(', 'b', 'or', 'c', ')'])


class TestParse(TestCase):
    def test_sanity(self):
        """
        Just checks if dataclass comparison works as expected.
        """
        self.assertEqual(Id('a'), Id('a'))
        self.assertEqual(Not(Id('a')), Not(Id('a')))
        self.assertEqual(And(Id('a'), Id('b')), And(Id('a'), Id('b')))
        self.assertEqual(Or(Id('a'), Id('b')), Or(Id('a'), Id('b')))
        self.assertEqual(And(Id('a'), Or(Id('b'), Id('C'))), And(Id('a'), Or(Id('b'), Id('C'))))

        self.assertNotEqual(Id('a'), Id('b'))
        self.assertNotEqual(Id('a'), Not(Id('a')))
        self.assertNotEqual(And(Id('a'), Id('b')), Or(Id('a'), Id('b')))
        self.assertNotEqual(And(Id('a'), Id('b')), And(Id('a'), Id('c')))
        self.assertNotEqual(Or(Id('a'), Id('b')), Or(Id('a'), Id('c')))
        self.assertNotEqual(And(Id('a'), Or(Id('b'), Id('C'))), Or(And(Id('a'), Id('b')), Id('C')))

    def test_simple(self):
        self.assertEqual(compile('a'), Id('a'))
        self.assertEqual(compile('A'), Id('A'))

        self.assertEqual(compile('not a'), Not(Id('a')))
        self.assertEqual(compile('not A'), Not(Id('A')))

        self.assertEqual(compile('a and b'), And(Id('a'), Id('b')))
        self.assertEqual(compile('a and b and c'), And(And(Id('a'), Id('b')), Id('c')))
        self.assertEqual(compile('a and b and c and d'), And(And(And(Id('a'), Id('b')), Id('c')), Id('d')))

        self.assertEqual(compile('a or b'), Or(Id('a'), Id('b')))
        self.assertEqual(compile('a or b or c'), Or(Id('a'), Or(Id('b'), Id('c'))))
        self.assertEqual(compile('a or b or c or d'), Or(Id('a'), Or(Id('b'), Or(Id('c'), Id('d')))))

    def test_case_sensitivity(self):
        self.assertEqual(compile('NOT a'), Not(Id('a')))
        self.assertEqual(compile('a AND b'), And(Id('a'), Id('b')))
        self.assertEqual(compile('a OR b'), Or(Id('a'), Id('b')))

    def test_precedence(self):
        self.assertEqual(compile('a or b and c'), Or(Id('a'), And(Id('b'), Id('c'))))
        self.assertEqual(compile('a and b or c'), Or(And(Id('a'), Id('b')), Id('c')))

        self.assertEqual(compile('a and b or c and d'), Or(And(Id('a'), Id('b')), And(Id('c'), Id('d'))))

        self.assertEqual(compile('not a or b and c'), Or(Not(Id('a')), And(Id('b'), Id('c'))))
        self.assertEqual(compile('a or not b and c'), Or(Id('a'), And(Not(Id('b')), Id('c'))))
        self.assertEqual(compile('a or b and not c'), Or(Id('a'), And(Id('b'), Not(Id('c')))))

    def test_nots(self):
        self.assertEqual(compile('not a and b'), And(Not(Id('a')), Id('b')))
        self.assertEqual(compile('a and not b'), And(Id('a'), Not(Id('b'))))
        self.assertEqual(compile('not a and not b'), And(Not(Id('a')), Not(Id('b'))))

        self.assertEqual(compile('not a or b'), Or(Not(Id('a')), Id('b')))
        self.assertEqual(compile('a or not b'), Or(Id('a'), Not(Id('b'))))
        self.assertEqual(compile('not a or not b'), Or(Not(Id('a')), Not(Id('b'))))

    def test_parens(self):
        self.assertEqual(compile('(a)'), Id('a'))
        self.assertEqual(compile('not (a)'), Not(Id('a')))

        self.assertEqual(compile('(a and b)'), And(Id('a'), Id('b')))
        self.assertEqual(compile('((a) and (b))'), And(Id('a'), Id('b')))
        self.assertEqual(compile('(((a)) and ((b)))'), And(Id('a'), Id('b')))

        self.assertEqual(compile('a or (b and c)'), Or(Id('a'), And(Id('b'), Id('c'))))
        self.assertEqual(compile('(a and b) or c'), Or(And(Id('a'), Id('b')), Id('c')))

        self.assertEqual(compile('a and (b or c)'), And(Id('a'), Or(Id('b'), Id('c'))))
        self.assertEqual(compile('(a or b) and c'), And(Or(Id('a'), Id('b')), Id('c')))

        self.assertEqual(compile('(a and b) or (c and d)'), Or(And(Id('a'), Id('b')), And(Id('c'), Id('d'))))
        self.assertEqual(compile('(a and b) or (c and d) or (e and f)'), Or(And(Id('a'), Id('b')), Or(And(Id('c'), Id('d')), And(Id('e'), Id('f')))))

        self.assertEqual(compile('not (a and b)'), Not(And(Id('a'), Id('b'))))
        self.assertEqual(compile('a and (not b or c)'), And(Id('a'), Or(Not(Id('b')), Id('c'))))
        self.assertEqual(compile('a and not (b or c)'), And(Id('a'), Not(Or(Id('b'), Id('c')))))
        self.assertEqual(compile('not (a and b) or c'), Or(Not(And(Id('a'), Id('b'))), Id('c')))

    def test_precedence(self):
        self.assertEqual(compile('a and b or c'), compile('(a and b) or c'))
        self.assertEqual(compile('a or b and c'), compile('a or (b and c)'))

        self.assertEqual(compile('a or not b'), compile('a or (not b)'))
        self.assertEqual(compile('not a or b'), compile('(not a) or b'))

    def test_errors(self):
        with self.assertRaises(ExpressionSyntaxError):
            compile('')

        with self.assertRaises(ExpressionSyntaxError):
            compile('and')

        with self.assertRaises(ExpressionSyntaxError):
            compile('or')

        with self.assertRaises(ExpressionSyntaxError):
            compile('not')

        with self.assertRaises(ExpressionSyntaxError):
            compile('()')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a and')

        with self.assertRaises(ExpressionSyntaxError):
            compile('and a')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a or')

        with self.assertRaises(ExpressionSyntaxError):
            compile('or a')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a not')

        with self.assertRaises(ExpressionSyntaxError):
            compile('not and')

        with self.assertRaises(ExpressionSyntaxError):
            compile('not or')

        with self.assertRaises(ExpressionSyntaxError):
            compile('(a and b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a (and b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a and (b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a and b (')

        with self.assertRaises(ExpressionSyntaxError):
            compile(') a and b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a) and b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a and) b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a and b)')

        with self.assertRaises(ExpressionSyntaxError):
            compile('(a or b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a (or b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a or (b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a or b (')

        with self.assertRaises(ExpressionSyntaxError):
            compile(') a or b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a) or b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a or) b')

        with self.assertRaises(ExpressionSyntaxError):
            compile('a or b)')

        with self.assertRaises(ExpressionSyntaxError):
            compile('(a and b or c')

        with self.assertRaises(ExpressionSyntaxError):
            compile('((a and b) or c')

        with self.assertRaises(ExpressionSyntaxError):
            compile('(a and b) or c)')


class TestEval(TestCase):
    def test_eval_simple(self):
        self.assertEqual(evalexpr(Id('a'), {'a'}), True)
        self.assertEqual(evalexpr(Id('a'), set()), False)
        self.assertEqual(evalexpr(Not(Id('a')), {'a'}), False)
        self.assertEqual(evalexpr(Not(Id('a')), set()), True)

        self.assertEqual(evalexpr(Id('A'), {'a'}), False)

    def test_eval_and(self):
        expr = And(Id('a'), Id('b'))
        self.assertEqual(evalexpr(expr, {'a', 'b'}), True)
        self.assertEqual(evalexpr(expr, {'a'}), False)
        self.assertEqual(evalexpr(expr, {'b'}), False)
        self.assertEqual(evalexpr(expr, set()), False)

        expr = And(Not(Id('a')), Id('b'))
        self.assertEqual(evalexpr(expr, {'a', 'b'}), False)
        self.assertEqual(evalexpr(expr, {'a'}), False)
        self.assertEqual(evalexpr(expr, {'b'}), True)
        self.assertEqual(evalexpr(expr, set()), False)

        expr = Not(And(Id('a'), Id('b')))
        self.assertEqual(evalexpr(expr, {'a', 'b'}), False)
        self.assertEqual(evalexpr(expr, {'a'}), True)
        self.assertEqual(evalexpr(expr, {'b'}), True)
        self.assertEqual(evalexpr(expr, set()), True)

    def test_eval_or(self):
        expr = Or(Id('a'), Id('b'))
        self.assertEqual(evalexpr(expr, {'a', 'b'}), True)
        self.assertEqual(evalexpr(expr, {'a'}), True)
        self.assertEqual(evalexpr(expr, {'b'}), True)
        self.assertEqual(evalexpr(expr, set()), False)

        expr = Or(Not(Id('a')), Id('b'))
        self.assertEqual(evalexpr(expr, {'a', 'b'}), True)
        self.assertEqual(evalexpr(expr, {'a'}), False)
        self.assertEqual(evalexpr(expr, {'b'}), True)
        self.assertEqual(evalexpr(expr, set()), True)

        expr = Not(Or(Id('a'), Id('b')))
        self.assertEqual(evalexpr(expr, {'a', 'b'}), False)
        self.assertEqual(evalexpr(expr, {'a'}), False)
        self.assertEqual(evalexpr(expr, {'b'}), False)
        self.assertEqual(evalexpr(expr, set()), True)

    def test_eval_and_or(self):
        expr = And(Id('a'), Or(Id('b'), Id('c')))
        self.assertEqual(evalexpr(expr, {'a', 'b', 'c'}), True)
        self.assertEqual(evalexpr(expr, {'a', 'b'}), True)
        self.assertEqual(evalexpr(expr, {'a', 'c'}), True)
        self.assertEqual(evalexpr(expr, {'b', 'c'}), False)
        self.assertEqual(evalexpr(expr, {'a'}), False)
        self.assertEqual(evalexpr(expr, {'b'}), False)
        self.assertEqual(evalexpr(expr, {'c'}), False)
        self.assertEqual(evalexpr(expr, set()), False)

        expr = Or(Id('a'), And(Id('b'), Id('c')))
        self.assertEqual(evalexpr(expr, {'a', 'b', 'c'}), True)
        self.assertEqual(evalexpr(expr, {'a', 'b'}), True)
        self.assertEqual(evalexpr(expr, {'a', 'c'}), True)
        self.assertEqual(evalexpr(expr, {'b', 'c'}), True)
        self.assertEqual(evalexpr(expr, {'a'}), True)
        self.assertEqual(evalexpr(expr, {'b'}), False)
        self.assertEqual(evalexpr(expr, {'c'}), False)
        self.assertEqual(evalexpr(expr, set()), False)

        expr = Not(And(Id('a'), Or(Id('b'), Id('c'))))
        self.assertEqual(evalexpr(expr, {'a', 'b', 'c'}), False)
        self.assertEqual(evalexpr(expr, {'a', 'b'}), False)
        self.assertEqual(evalexpr(expr, {'a', 'c'}), False)
        self.assertEqual(evalexpr(expr, {'b', 'c'}), True)
        self.assertEqual(evalexpr(expr, {'a'}), True)
        self.assertEqual(evalexpr(expr, {'b'}), True)
        self.assertEqual(evalexpr(expr, {'c'}), True)
        self.assertEqual(evalexpr(expr, set()), True)

