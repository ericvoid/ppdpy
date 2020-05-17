# PPDPY

PPDPY - "Preprocessor Directives for Python" - is a minimal templating library.
Use code like preprocessor directives (or compiler instructions) to make a plain
text into dynamic template.

Currently there is only one type of directive: conditionals. The conditionals
accepts simple logic expressions with boolean symbols.

## Installing

    $ pip install ppdpy

This package is compatible with Python 3.6 and above.

## Quick Start

Suppose you have a template file named "mytemplate.txt" with the following contents:

```
line 1
#if a or b
line 2
#elif c
line 3
#else
line 4
#endif
line 5
```

Then this file can be rendered like this:

```python
>>> import ppdpy
>>> with open('mytemplate.txt') as f:
...     template = ppdpy.compile(f)
>>>
>>> print(template.render({'a'}))
line 1
line 2
line 5

>>> print(template.render({'b'}))
line 1
line 2
line 5

>>> print(template.render({'c'}))
line 1
line 3
line 5

>>> print(template.render({}))
line 1
line 4
line 5
```

The ppdpy module has the following functions:

* `compile(file)` compiles a file, and returns a template object that can be rendered later;
* `compiles(text)` compiles a string, and returns a template object that can be rendered later.
* `render(file, symbols)` render a file using the given set of symbols, and returns the rendered string;
* `renders(text, symbols)` render a string using the given set of symbols, and returns the rendered string;

### Example use case - SQL

This template engine can be used with any kind of text files, but the main use
case this library was implemented for was to manipulate raw SQL files.

PPDPY is minimal, but it can prove itself handy when used with raw SQL
queries. The following example outputs queries to be used with pyscopg2
(PostgreSQL).

```sql
select channel.id, channel.name, membership.joined_at

#if select_unread_count
    ,(select coalesce(count(*), 0) from messages m
      where m.channel_id = channel.id
        and m.sender_id != chat_user.id
        and (last_read.id IS NULL OR m.sent_at > last_read.sent_at)
    ) as unread_count
#endif

from channel

    inner join membership
    on membership.channel_id = channel.id

    inner join chatuser
    on chat_user.id = membership.chat_user_id

#if select_unread_count
    left join message last_read
    on last_read.id = membership.last_read_id
    and last_read.channel_id = channel.id
#endif

where chat_user.id = %(user_id)s

#if filter_by_status
    and channel.status = %(status_filter)s
#endif

order by
#if order_by_join_date
    membership.joined_at
#elif order_by_readcount
    4
#else
    channel.name
#endif

#if sort_descending
    DESC
#else
    ASC
#endif
```

Usually there are very complex SQL commands that are hard to write using ORMs.
Either ORMs does not have the necessary features to write this kind of queries at
all, or the resulting code is unmaintainable - very complicated and unreadable,
and certainly very difficult fix or change it later.

And sometimes using Raw SQL is not viable, because ORMs allows us to dynamically
change the selected columns, the joined tables, the where filters and the
sorting columns and directions. A more "traditional" SQL approach would be to
create multiple SQL files (or strings) for the combinations of the desired
queries, but you would end up with lots of similar files  to do slightly
different things (what is also bad for maintainability).

Another solution would be to use raw SQL with "manual" string manipulation. But
frankly, this is not nice and also bad for maintainability.

Since PPDPY considers its input as plain text, any kind of text file can be used (not just SQL).


## API

The `ppdpy` module contains the following functions.

`compile(file)` compiles the contents of a file and returns a `Template` object,
which can be used to render it later.

```python
>>> import ppdpy
>>> with open('testfile.txt') as f:
...     template = ppdpy.compile(f)
>>>
>>> template.render({'test'})
foobar
test block reached
```

`compiles(text)` compiles the given string and returns a `Template` object.

```python
>>> import ppdpy
>>> template = ppdpy.compiles("""foobar
#if test
test block reached
#endif
""")
>>>
>>> template.render({'test'})
foobar
test block reached
>>> template.render({})
foobar
```

`render(file, symbols)` receives a file pointer and a set of strings,
and returns the rendered string. This is an alias to
`compile(file).render(symbols)`.

`renders(text, symbols)` the same as `render`, but receives a string
at the first argument. This is an alias to `compiles(text).render(symbols)`.

`set_directive_prefix(prefix)` use this to change the directive prefix, if
the file type you want to render uses the `#` char as special (like comments).
This function will set the directive prefix globally.

The prefix can be of any length, containing any char of the following: digits,
ASCII letters and punctuation (refer to Python's string module).
Invisible characters (like spaces, tabs and line breaks) are not allowed.

### Template object

The template object only has the following method:

`render(self, symbols)` renders the template with the given symbols (set of
strings) and returns the rendered string. The set of strings is used to evaluate
the expressions in the template, and each string a symbol that computes to
`True`. Symbols are computed to `False` when they are not present in the strings
set.

Other iterable types are accepted on the `symbols` argument. They are converted
to `set` internally. Also, dictionaries are accepted. In this case the keys of
the dictionary will be used as symbols. Internally, it runs 
`symbols = set(symbols.keys())`.


## Exceptions

`ppdpy.exceptions.DirectiveSyntaxError` is raised when there are errors related to directives.

`ppdpy.exceptions.ExpressionSyntaxError` is raised when there are errors related to the boolean expressions.

## Directives

All directives starts with `#` char, and it must be the first visible char in
the line to be considered as a directive. For example, all the following lines are
considered as directives:

    #if something
        #if another_thing
        #else
      #endif
    #endif

The available directives are:

* `#if` starts a conditional block;
* `#elif` is an else-if conditional block, to create composite conditional blocks (optional);
* `#else` is the "fallback" conditional block - if none of the previous blocks calculates to True,
  then this block is rendered (optional);
* `#endif` ends a conditional block.

The directives are **case insensitive**, so `#IF something` is equal to `#if something`.

### Examples:

Simple conditional block:

    #if my_symbol
    foobar
    #endif

Simple conditional with else block:

    #if my_symbol
    foobar
    #else
    noop
    #endif

Conditional block with elif:

    #if my_symbol
    foobar
    #elif other_symbol
    fuzzbuzz
    #endif

Conditional block with elif and else:

    #if my_symbol
    foobar
    #elif other_symbol
    fuzzbuzz
    #else
    noop
    #endif

Nested conditional blocks are supported. For example:

    #if a and b
        foo
        #if c or d
            bar
        #else
            test
        #endif
    #endif

## Expressions

The expressions supported by `#if` and `#elif` directives are basic boolean logic with
these operators: `and`, `or` and `not`. These operators are **case insensitive**
Examples of supported expressions:

* `#if a`
* `#if not a`
* `#if a and b`
* `#if a and not b`
* `#if a or b`
* `#if a or not b`
* `#if a and (b or c)`
* `#if a and not (b or c)`
* `#IF a AND NOT (b OR c)`
* etc.

The `not` and `and` operators has higher precedence, and the `or` operator has lower
precedence. So `a and b or c` is the same as `(a and b) or c`, and `not a or b`
is the same as `(not a) or b`.

The symbols are simple strings, and only the following characters are not considered as
part of a symbol: parentheses, whitespace, tabs, linebreaks, and other
invisible characters. The symbols are **case sensitive**.

When rendering, the symbols in the expression are checked against the symbols set
passed during the "render" call. For example, when the `#if foobar` expression
is executed, it checks if the "foobar" string is present on the symbols set.

Examples of supported symbols:

* `#if a`
* `#if a1`
* `#if mysymbol`
* `#if MySymbol`
* `#if MYSYMBOL`
* `#if my_symbol`
* `#if my-symbol`
* `#if MY_SYMBOL`
* `#if MY-SYMBOL`

Each of the symbols above is considered a distinct one.

More exotic symbols such as `$my@symbol!` or `{my[symbol]}?` can work, but it
is advised to not use them since it may change in the future.

Parenthesis in the symbols will produce errors. `#if my(symbol)` is parsed as
`#if my ( symbol )`, and `DirectiveSyntaxError` will be thrown.
