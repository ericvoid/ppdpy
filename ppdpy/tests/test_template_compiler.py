from unittest import TestCase

from ppdpy import renders
from ppdpy.exceptions import ExpressionSyntaxError, DirectiveSyntaxError


class TestTemplates(TestCase):
    def test(self):
        self.assertEqual(renders('foobar', set()), 'foobar')
        self.assertEqual(renders('foobar\n', set()), 'foobar\n')

        template = """
foobar
"""
        self.assertEqual(renders(template, set()), template)

        template = """
line1
line2
line3
"""
        self.assertEqual(renders(template, set()), template)

        template = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. In euismod metus sed
lacus sagittis, vitae egestas ipsum congue. Vestibulum vehicula consectetur
aliquet. Aenean tincidunt, mi vel pulvinar ullamcorper, sem velit bibendum
velit, a condimentum purus lorem vitae lectus.

Phasellus enim augue, maximus sit amet felis non, varius egestas erat. Nunc
ornare tempor imperdiet. Quisque ultrices efficitur nunc, in iaculis mauris
iaculis dapibus.

Vivamus sit amet pellentesque eros. Nulla facilisi. Morbi nec urna lacus.
Phasellus interdum mauris porta, vehicula neque quis, accumsan nunc. Nullam a
purus mi. Sed ultricies vulputate massa, non tincidunt nibh molestie quis.
"""
        self.assertEqual(renders(template, set()), template)

    def test_if(self):
        template = """
line 1
#if x
line 2
#endif
line 3
"""
        result = """
line 1
line 2
line 3
"""
        self.assertEqual(renders(template, set('x')), result)

        result = """
line 1
line 3
"""
        self.assertEqual(renders(template, set()), result)
        self.assertEqual(renders(template, set('y')), result)

        template = """
line 1
line 2
#if x
line 3
line 4
#endif
line 5
line 6
"""
        result = """
line 1
line 2
line 3
line 4
line 5
line 6
"""
        self.assertEqual(renders(template, set('x')), result)

        result = """
line 1
line 2
line 5
line 6
"""
        self.assertEqual(renders(template, set()), result)


    def test_if_else(self):
        template = """
line 1
#if x
line 2
#else
line 3
#endif
line 4
"""
        result = """
line 1
line 2
line 4
"""
        self.assertEqual(renders(template, set('x')), result)

        result = """
line 1
line 3
line 4
"""
        self.assertEqual(renders(template, set()), result)

    def test_if_elif(self):
        template = """
#if x
line 1
#elif y
line 2
#endif
"""
        result = """
line 1
"""
        self.assertEqual(renders(template, set('x')), result)

        result = """
line 2
"""
        self.assertEqual(renders(template, set('y')), result)

        template = """
#if x
line 1
#elif y
line 2
#elif z
line 3
#endif
"""
        result = """
line 1
"""
        self.assertEqual(renders(template, set('x')), result)

        result = """
line 2
"""
        self.assertEqual(renders(template, set('y')), result)

        result = """
line 3
"""
        self.assertEqual(renders(template, set('z')), result)

    def test_if_elif_else(self):
        template = """
#if x
line 1
#elif y
line 2
#else
line 3
#endif
"""
        result = """
line 1
"""
        self.assertEqual(renders(template, set('x')), result)

        result = """
line 2
"""
        self.assertEqual(renders(template, set('y')), result)

        result = """
line 3
"""
        self.assertEqual(renders(template, set()), result)

    def test_empty_if_elif_else(self):
        template = """line 1
#if x
#elif y
#else
#endif
"""
        result = """line 1
"""
        self.assertEqual(renders(template, set('x')), result)
        self.assertEqual(renders(template, set('y')), result)
        self.assertEqual(renders(template, set()), result)

    def test_if_expr(self):
        template = """
#if x and (y or z)
line 1
#else
line 2
#endif
"""
        result = """
line 1
"""
        self.assertEqual(renders(template, {'x', 'y', 'z'}), result)
        self.assertEqual(renders(template, {'x', 'y'}), result)
        self.assertEqual(renders(template, {'x', 'z'}), result)

        result = """
line 2
"""
        self.assertEqual(renders(template, set()), result)
        self.assertEqual(renders(template, set('x')), result)
        self.assertEqual(renders(template, set('y')), result)
        self.assertEqual(renders(template, set('z')), result)
        self.assertEqual(renders(template, {'y', 'z'}), result)

        template = """
#if x and y
line 1
#elif x or y
line 2
#else
line 3
#endif
"""
        result = """
line 1
"""
        self.assertEqual(renders(template, {'x', 'y'}), result)

        result = """
line 2
"""
        self.assertEqual(renders(template, {'x'}), result)
        self.assertEqual(renders(template, {'y'}), result)

        result = """
line 3
"""
        self.assertEqual(renders(template, set()), result)
        self.assertEqual(renders(template, set('z')), result)

    def test_if_case_insensitive(self):
        template = """
#IF x AND y
line 1
#ELIF x OR y
line 2
#ELSE
line 3
#ENDIF
"""
        result = """
line 1
"""
        self.assertEqual(renders(template, {'x', 'y'}), result)

        result = """
line 2
"""
        self.assertEqual(renders(template, {'x'}), result)
        self.assertEqual(renders(template, {'y'}), result)

        result = """
line 3
"""
        self.assertEqual(renders(template, set()), result)
        self.assertEqual(renders(template, set('z')), result)

    def test_nested_if(self):
        template = """
#if x
line 1
    #if y
line 2
    #else
line 3
    #endif
line 4
#endif
"""
        result = """
line 1
line 3
line 4
"""
        self.assertEqual(renders(template, set('x')), result)

        result = """
line 1
line 2
line 4
"""
        self.assertEqual(renders(template, {'x', 'y'}), result)

        template = """
line 1
#if x
    #if y
    #else
    #endif
#else
#endif
"""
        result = "\nline 1\n"
        self.assertEqual(renders(template, {'x', 'y'}), result)
        self.assertEqual(renders(template, {'y'}), result)
        self.assertEqual(renders(template, {'y'}), result)
        self.assertEqual(renders(template, {}), result)

    def test_error(self):
        template = """
#if foo
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
#if 
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
#if
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
#if foo and
#endif
"""
        with self.assertRaises(ExpressionSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
#if foo
#else
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
#if foo
#elif bar
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
line 1
#if foo
#elif 
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
line 1
#if foo
#elif
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
line 1
#if foo
#elif bar
#else
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
line 1
#if foo
    #if foo
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
line 1
#if foo
    #if foo
    #else
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
line 1
#if foo
    #if foo
    #elif
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')

        template = """
line 1
#if foo
    #if foo
    #elif
    #else
#endif
"""
        with self.assertRaises(DirectiveSyntaxError):
            self.assertEqual(renders(template, {'foo'}), '')
