from ppdpy.template_compiler import compile as compile_template, LINEBREAK


def compile(file):
    return compile_template(file)


def compiles(text):
    return compile_template(text.split(LINEBREAK))


def render(file, symbols):
    return compile(file).render(symbols)


def renders(text, symbols):
    return compiles(text).render(symbols)


def set_directive_prefix(prefix):
    import ppdpy.template_compiler
    import string

    if not isinstance(prefix, str):
        raise ValueError

    allowed_chars = string.digits + string.ascii_letters + string.punctuation
    for c in prefix:
        if c not in allowed_chars:
            raise ValueError

    ppdpy.template_compiler.set_directive_prefixes(prefix)
