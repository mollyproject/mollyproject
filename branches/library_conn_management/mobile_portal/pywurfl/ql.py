# pywurfl QL - Wireless Universal Resource File Query Language in Python
# Copyright (C) 2006-2009 Armand Lynch
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Armand Lynch <lyncha@users.sourceforge.net>

__doc__ = \
"""
pywurfl Query Language

pywurfl QL is a WURFL query language that looks very similar to SQL.

Language Definition
===================

Select statement
================

    select (device|id|ua)
    ---------------------

    The select statement consists of the keyword 'select' followed by the
    select type which can be one of these keywords: 'device', 'ua', 'id'.
    The select statement is the first statement in all queries.

    device
    ------
    When 'select' is followed by the keyword 'device', a device object will
    be returned for each device that matches the 'where' expression
    (see below).

    ua
    --
    When 'select' is followed by the keyword 'ua', an user-agent string
    will be returned for each device that matches the 'where' expression
    (see below).

    id
    --
    When 'select' is followed by the keyword 'id', a WURFL id string will be
    returned for each device that matches the 'where' expression (see below).


Where statement
===============

    where condition
    ---------------
    where condition and/or condition
    --------------------------------
    where any/all and/or condition
    ------------------------------

    The where statement follows a select statement and can consist of the
    following elements: 'where condition', 'any statement', 'all statement'.

    Where condition
    ---------------
    A where condition consists of a capability name followed by a test
    operator followed by a value. For example, "ringtone = true".

    Any statement
    -------------
    An any statement consists of the keyword 'any' followed by a
    parenthesized, comma delimited list of capability names, followed by
    a test operator and then followed by a value. All capabilities
    listed in an any statement will be 'ored' together. There must be a
    minimum of two capabilities listed.

    For example: "any(ringtone_mp3, ringtone_wav) = true".

    All statement
    -------------
    An all statement consists of the keyword 'all' followed by a
    parenthesized, comma delimited list of capability names, followed by
    a test operator and then followed by a value. All capabilities
    listed in an all statement will be 'anded' together. There must be a
    minimum of two capabilities listed.

    For example: "all(ringtone_mp3, ringtone_wav) = true".

    Test operators
    --------------
    The following are the test operators that the query language can
    recognize::

        = != < > >= <=

    Comparing strings follow Python's rules.

    Values
    ------
    Test values can be integers, strings in quotes and the tokens
    "true" or "false" for boolean tests.


Binary operators
================

    There are two binary operators defined in the language "and" and "or".
    They can be used between any where statement tests and follow
    conventional precedence rules::

      ringtone=true or ringtone_mp3=false and preferred_markup="wml_1_1"
                                -- becomes --
      (ringtone=true or (ringtone_mp3=false and preferred_markup="wml_1_1"))


Example Queries
===============

    select id where ringtone=true

    select id where ringtone=false and ringtone_mp3=true

    select id where rows > 3

    select id where all(ringtone_mp3, ringtone_aac, ringtone_qcelp)=true

    select ua where preferred_markup = "wml_1_1"


EBNF
====

query := select_statement where_statement

select_statement := 'select' ('device' | 'id' | 'ua')

where_statement := 'where' + where_expression

where_expression := where_test (boolop where_test)*

where_test := (any_statement | all_statement | expr_test)

any_statement := 'any' '(' expr_list ')' operator expr

all_statement := 'all' '(' expr_list ')' operator expr

capability := alphanums ('_' alphanums)*

expr_test := expr operator expr

expr_list := expr (',' expr)*

expr := types attributes_methods_concat | capability attributes_methods_concat

attributes_methods_concat := ('.' method '(' method_args? ')')*

method_args := (method_arg (',' method_arg)*)

method_arg := (types | expr)

method := ('_' alphanums)*

operator := ('='|'!='|'<'|'>'|'>='|'<=')

types := (<quote> string <quote> | integer | boolean)

boolean := ('true' | 'false')

boolop := ('and' | 'or')
"""

import re
import operator

from pyparsing import (CaselessKeyword, Forward, Group, ParseException,
                       QuotedString, StringEnd, Suppress, Word, ZeroOrMore,
                       alphanums, alphas, nums, oneOf, delimitedList)

from pywurfl.exceptions import WURFLException


__author__ = "Armand Lynch <lyncha@users.sourceforge.net>"
__contributors__ = "Gabriele Fantini <gabriele.fantini@staff.dada.net>"
__copyright__ = "Copyright 2006-2009, Armand Lynch"
__license__ = "LGPL"
__url__ = "http://celljam.net/"
__all__ = ['QueryLanguageError', 'QL']


class QueryLanguageError(WURFLException):
    """Base exception class for pywurfl.ql"""
    pass


def _toNum(s, l, toks):
    """Convert to pywurfl number type"""
    n = toks[0]
    try:
        return TypeNum(int(n))
    except ValueError, e:
        return TypeNum(float(n))


def _toBool(s, l, toks):
    """Convert to pywurfl boolean type"""
    val = toks[0]
    if val.lower() == 'true':
        return TypeBool(True)
    elif val.lower() == 'false':
        return TypeBool(False)
    else:
        raise QueryLanguageError("Invalid boolean value '%s'" % val)


def _toStr(s, l, toks):
    """Convert to pywurfl string type"""
    val = toks[0]
    return TypeStr(val)


class _Type:
    def __init__(self, py_value):
        self.py_value = py_value

    def __getattr__(self, method):
        return getattr(self.py_value, method)


class TypeNone(_Type):
    pass


class TypeNum(_Type):
    pass


class TypeStr(_Type):
    def substr(self, begin, end):
        try:
            return self.py_value[begin:end]
        except IndexError, e:
            return None

    def _match(self, regex, num=0, flags=0):
        if re.compile(regex, flags).match(self.py_value, num) is None:
            return False
        else:
            return True

    def match(self, regex, num=0):
        return self._match(regex, num)

    def imatch(self, regex, num=0):
        return self._match(regex, num, re.IGNORECASE)


class TypeBool(_Type):
    pass


class TypeList(_Type):
    def getitem(self, i):
        try:
            return self.__getitem__(i)
        except IndexError, e:
            return None

def define_language():
    """
    Defines the pywurfl query language.

    @rtype: pyparsing.ParserElement
    @return: The definition of the pywurfl query language.
    """

    # Data types to bind to python objects
    integer = Word(nums).setParseAction(_toNum)
    boolean = (CaselessKeyword("true") | CaselessKeyword("false")).setParseAction(_toBool)
    string = (QuotedString("'") | QuotedString('"')).setParseAction(_toStr)
    types = (integer | boolean | string)('value')

    capability = Word(alphas, alphanums + '_')('capability')

    # Select statement
    select_token = CaselessKeyword("select")
    ua_token = CaselessKeyword("ua")
    id_token = CaselessKeyword("id")
    device_token = CaselessKeyword("device")
    select_type = (device_token | ua_token | id_token)("type")
    select_clause = select_token + select_type
    select_statement = Group(select_clause)("select")

    expr = Forward()

    # class methods
    method_arg = (types | Group(expr))
    method_args = Group(ZeroOrMore(delimitedList(method_arg)))('method_args')

    # class attribute
    attribute = Word(alphas + '_', alphanums + '_')("attribute")
    attribute_call = (attribute + Suppress('(') + method_args +
                      Suppress(')'))("attribute_call")
    # To support method and attribute list like .lower().upper()
    attribute_concat = Group(ZeroOrMore(Group(Suppress('.') + (attribute_call | attribute))))('attribute_concat')

    expr << Group(types + attribute_concat | capability + attribute_concat)('expr')

    binop = oneOf("= != < > >= <=", caseless=True)("operator")
    and_ = CaselessKeyword("and")
    or_ = CaselessKeyword("or")

    expr_list = (expr + ZeroOrMore(Suppress(',') + expr))

    # Any test
    any_token = CaselessKeyword("any")
    any_expr_list = expr_list("any_expr_list")
    any_statement = (any_token + Suppress('(') + any_expr_list + Suppress(')') +
                     binop + expr("rexpr"))('any_statement')

    # All test
    all_token = CaselessKeyword("all")
    all_expr_list = expr_list("all_expr_list")
    all_statement = (all_token + Suppress('(') + all_expr_list + Suppress(')') +
                     binop + expr("rexpr"))('all_statement')

    # Capability test
    expr_test = expr('lexpr') + binop + expr('rexpr')

    # WHERE statement
    boolop = (and_ | or_)('boolop')
    where_token = CaselessKeyword("where")

    where_test = (all_statement | any_statement | expr_test)('where_test')
    where_expression = Forward()
    where_expression << Group(where_test + ZeroOrMore(boolop + where_expression))('where_expression')

    #where_expression << (Group(where_test + ZeroOrMore(boolop +
    #                                                   where_expression) +
    #                           StringEnd())('where'))
    #where_expression = (Group(where_test + ZeroOrMore(boolop + where_test) +
    #                    StringEnd())('where'))

    where_statement = where_token + where_expression

    # Mon Jan  1 12:35:56 EST 2007
    # If there isn't a concrete end to the string pyparsing will not parse
    # query correctly
    return select_statement + where_statement + '*' + StringEnd()


def get_operators():
    """
    Returns a dictionary of operator mappings for the query language.

    @rtype: dict
    """

    def and_(func1, func2):
        """
        Return an 'anding' function that is a closure over func1 and func2.
        """
        def and_tester(value):
            """Tests a device by 'anding' the two following functions:"""
            return func1(value) and func2(value)
        return and_tester

    def or_(func1, func2):
        """
        Return an 'oring' function that is a closure over func1 and func2.
        """
        def or_tester(value):
            """Tests a device by 'oring' the two following functions:"""
            return func1(value) or func2(value)
        return or_tester

    return {'=':operator.eq, '!=':operator.ne, '<':operator.lt,
            '>':operator.gt, '>=':operator.ge, '<=':operator.le,
            'and':and_, 'or':or_}


ops = get_operators()


def expr_test(lexpr, op, rexpr):
    """
    Returns an exp test function.

    @param lexpr: An expr
    @type lexpr: expr
    @param op: A binary test operator
    @type op: string
    @param rexpr: An expr
    @type rexpr: expr

    @rtype: function
    """

    def expr_tester(devobj):

        def evaluate(expression):
            value = None
            if expression.keys() == ['expr']:
                expression = expression.expr
            # check wheather the expression is a capability or not
            if 'capability' in expression.keys():
                capability = expression.capability
                try:
                    py_value = getattr(devobj, capability)
                except AttributeError, e:
                    raise QueryLanguageError("Invalid capability '%s'" %
                                             capability)

                if isinstance(py_value, bool):
                    value = TypeBool(py_value)
                elif isinstance(py_value, int):
                    value = TypeNum(py_value)
                elif isinstance(py_value, str):
                    value = TypeStr(py_value)
                else:
                    raise QueryLanguageError("Unknown type '%s'" %
                                             py_value.__class__)
            else:
                value = expression.value

            for attribute in expression.attribute_concat:
                py_value = None
                if 'attribute_call' in attribute.keys():
                    method_name = attribute.attribute_call.attribute
                    method_args = []
                    for method_arg in attribute.attribute_call.method_args:
                        method_arg_value = None
                        try:
                            method_arg_value = evaluate(method_arg.expression)
                        except AttributeError, e:
                            method_arg_value = method_arg

                        method_args.append(method_arg_value.py_value)

                    try:
                        attr = getattr(value, method_name)
                        py_value = attr(*method_args)
                    except (AttributeError, TypeError), e:
                        msg = "'%s' object has no callable attribute '%s'"
                        raise QueryLanguageError(msg %
                                                 (type(value.py_value).__name__,
                                                  method_name))
                elif 'attribute' in attribute.keys():
                    try:
                        py_value = getattr(value, attribute.attribute)
                    except AttributeError, e:
                        raise QueryLanguageError(str(e))
                    if callable(py_value):
                        msg = "'%s' object has no attribute '%s'"
                        raise QueryLanguageError(msg %
                                                 (type(value.py_value).__name__,
                                                  attribute.attribute))
                else:
                    raise QueryLanguageError('query syntax error')

                if isinstance(py_value, bool):
                    value = TypeBool(py_value)
                elif py_value is None:
                    value = TypeNone(py_value)
                elif isinstance(py_value, int):
                    value = TypeNum(py_value)
                elif isinstance(py_value, str):
                    value = TypeStr(py_value)
                elif isinstance(py_value, (list, tuple)):
                    value = TypeList(py_value)
                else:
                    raise QueryLanguageError("Unknown type '%s'" %
                                             py_value.__class__)

            return value

        lvalue = evaluate(lexpr)
        rvalue = evaluate(rexpr)
        return ops[op](lvalue.py_value, rvalue.py_value)

    return expr_tester


def combine_funcs(funcs):
    """
    Combines a list of functions with binary operators.

    @param funcs: A python list of function objects with descriptions of
                  binary operators interspersed.

                  For example [func1, 'and', func2, 'or', func3]
    @type funcs: list
    @rtype: function
    """

    while len(funcs) > 1:
        try:
            f_index = funcs.index('and')
            op = ops['and']
        except ValueError:
            try:
                f_index = funcs.index('or')
                op = ops['or']
            except ValueError:
                break
        combined = op(funcs[f_index - 1], funcs[f_index + 1])
        funcs = funcs[:f_index-1] + [combined] + funcs[f_index + 2:]
    return funcs[0]


def reduce_funcs(func, seq):
    """
    Reduces a sequence of function objects to one function object by applying
    a binary function recursively to the sequence::

        In:
            func = and
            seq = [func1, func2, func3, func4]
        Out:
            and(func1, and(func2, and(func3, func4)))

    @param func: A function that acts as a binary operator.
    @type func: function
    @param seq: An ordered sequence of function objects
    @type seq: list
    @rtype: function
    """

    if seq[1:]:
        return func(seq[0], reduce_funcs(func, seq[1:]))
    else:
        return seq[0]


def reduce_statement(exp):
    """
    Produces a function that represents the "any" or "all" expression passed
    in by exp::

        In:
            any(ringtone_mp3, ringtone_awb) = true
        Out:
            ((ringtone_mp3 = true) or (ringtone_awb = true))

    @param exp: The result from parsing an 'any' or 'all' statement.
    @type exp: pyparsing.ParseResults
    @rtype: function
    """

    funcs = []
    if exp.any_statement:
        for expr in exp.any_statement.any_expr_list:
            funcs.append(expr_test(expr, exp.operator, exp.rexpr))
        return reduce_funcs(ops['or'], funcs)
    elif exp.all_statement:
        for expr in exp.all_statement.all_expr_list:
            funcs.append(expr_test(expr, exp.operator, exp.rexpr))
        return reduce_funcs(ops['and'], funcs)


def test_generator(ql_result):
    """
    Produces a function that encapsulates all the tests from a where
    statement and takes a Device class or object as a parameter::

        In (a result object from the following query):
          select id where ringtone=true and any(ringtone_mp3, ringtone_awb)=true

        Out:
          def func(devobj):
              if (devobj.ringtone == True and
                  (devobj.ringtone_mp3 == True or
                   devobj.ringtone_awb == True)):
                  return True
              else:
                  return False
          return func

    @param ql_result: The result from calling pyparsing.parseString()
    @rtype: function
    """

    funcs = []
    where_test = ql_result.where_expression
    while where_test:
        if where_test.any_statement or where_test.all_statement:
            func = reduce_statement(where_test)
        else:
            func = expr_test(where_test.lexpr, where_test.operator,
                             where_test.rexpr)

        boolop = where_test.boolop
        if boolop:
            funcs.extend([func, boolop])
        else:
            funcs.append(func)
        where_test = where_test.where_expression
    return combine_funcs(funcs)


def QL(devices):
    """
    Return a function that can run queries against the WURFL.

    @param devices: The device class hierarchy from pywurfl
    @type devices: pywurfl.Devices
    @rtype: function
    """

    language = define_language()

    def query(qstr, instance=True):
        """
        Return a generator that filters the pywurfl.Devices instance by the
        query string provided in qstr.

        @param qstr: A query string that follows the pywurfl.ql language
                     syntax.
        @type qstr: string
        @param instance: Used to select that you want an instance instead of a
                         class.
        @type instance: boolean
        @rtype: generator
        """
        qstr = qstr.replace('\n', ' ').replace('\r', ' ') + '*'
        try:
            qres = language.parseString(qstr)
            tester = test_generator(qres)
            if qres.select.type == 'ua':
                return (x.devua for x in devices.devids.itervalues()
                        if tester(x))
            elif qres.select.type == 'id':
                return (x.devid for x in devices.devids.itervalues()
                        if tester(x))
            else:
                if instance:
                    return (x() for x in devices.devids.itervalues()
                            if tester(x))
                else:
                    return (x for x in devices.devids.itervalues()
                            if tester(x))
        except ParseException, exception:
            raise QueryLanguageError(str(exception))
    setattr(devices, 'query', query)
    return query

