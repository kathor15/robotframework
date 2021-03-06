import unittest
import sys

from robot.variables import Variables
from robot.errors import DataError
from robot.utils.asserts import assert_equal, assert_raises
from robot.utils import JYTHON


SCALARS = ['${var}', '${  v A  R }']
LISTS = ['@{var}', '@{  v A  R }']
NOKS = ['var', '$var', '${var', '${va}r', '@{va}r', '@var', '%{var}', ' ${var}',
        '@{var} ', '\\${var}', '\\\\${var}', 42, None, ['${var}'], DataError]


# Simple objects needed when testing assigning objects to variables.
# JavaObject lives in '../../acceptance/testdata/libraries'

class PythonObject:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def __str__(self):
        return '(%s, %s)' % (self.a, self.b)
    __repr__ = __str__

if JYTHON:
    import JavaObject


class TestVariables(unittest.TestCase):

    def setUp(self):
        self.varz = Variables()

    def test_set(self):
        value = ['value']
        for var in SCALARS + LISTS:
            self.varz[var] = value
            assert_equal(self.varz[var], value)
            assert_equal(self.varz[var.lower().replace(' ', '')] , value)
            self.varz.clear()

    def test_set_invalid(self):
        for var in NOKS:
            assert_raises(DataError, self.varz.__setitem__, var, 'value')

    def test_set_scalar(self):
        for var in SCALARS:
            for value in ['string', '', 10, ['hi', 'u'], ['hi', 2],
                          {'a': 1, 'b': 2}, self, None, unittest.TestCase]:
                self.varz[var] = value
                assert_equal(self.varz[var], value)

    def test_set_list(self):
        for var in LISTS:
            for value in [[], [''], ['str'], [10], ['hi', 'u'], ['hi', 2],
                          [{'a': 1, 'b': 2}, self, None]]:
                self.varz[var] = value
                assert_equal(self.varz[var], value)
                self.varz.clear()

    def test_replace_scalar(self):
        self.varz['${foo}'] = 'bar'
        self.varz['${a}'] = 'ari'
        for inp, exp in [('${foo}', 'bar'),
                         ('${a}', 'ari'),
                         ('${a', '${a'),
                         ('', ''),
                         ('hii', 'hii'),
                         ("Let's go to ${foo}!", "Let's go to bar!"),
                         ('${foo}ba${a}-${a}', 'barbaari-ari')]:
            assert_equal(self.varz.replace_scalar(inp), exp)

    def test_replace_list(self):
        self.varz['@{L}'] = ['v1', 'v2']
        self.varz['@{E}'] = []
        self.varz['@{S}'] = ['1', '2', '3']
        for inp, exp in [(['@{L}'], ['v1', 'v2']),
                         (['@{L}', 'v3'], ['v1', 'v2', 'v3']),
                         (['v0', '@{L}', '@{E}', 'v@{S}[2]'], ['v0', 'v1', 'v2', 'v3']),
                         ([], []),
                         (['hi u', 'hi 2', 3], ['hi u','hi 2', 3])]:
            assert_equal(self.varz.replace_list(inp), exp)

    def test_replace_list_in_scalar_context(self):
        self.varz['@{list}'] = ['v1', 'v2']
        assert_equal(self.varz.replace_list(['@{list}']), ['v1', 'v2'])
        assert_equal(self.varz.replace_list(['-@{list}-']), ["-['v1', 'v2']-"])

    def test_replace_list_item(self):
        self.varz['@{L}'] = ['v0', 'v1']
        assert_equal(self.varz.replace_list(['@{L}[0]']), ['v0'])
        assert_equal(self.varz.replace_scalar('@{L}[1]'), 'v1')
        assert_equal(self.varz.replace_scalar('-@{L}[0]@{L}[1]@{L}[0]-'), '-v0v1v0-')
        self.varz['@{L2}'] = ['v0', ['v11', 'v12']]
        assert_equal(self.varz.replace_list(['@{L2}[0]']), ['v0'])
        assert_equal(self.varz.replace_list(['@{L2}[1]']), [['v11', 'v12']])
        assert_equal(self.varz.replace_scalar('@{L2}[0]'), 'v0')
        assert_equal(self.varz.replace_scalar('@{L2}[1]'), ['v11', 'v12'])
        assert_equal(self.varz.replace_list(['@{L}[0]', '@{L2}[1]']), ['v0', ['v11', 'v12']])

    def test_replace_dict_item(self):
        self.varz['&{D}'] = {'a': 1, 2: 'b'}
        assert_equal(self.varz.replace_list(['&{D}[a]']), [1])
        assert_equal(self.varz.replace_scalar('&{D}[${2}]'), 'b')

    def test_replace_non_strings(self):
        self.varz['${d}'] = {'a': 1, 'b': 2}
        self.varz['${n}'] = None
        assert_equal(self.varz.replace_scalar('${d}'), {'a': 1, 'b': 2})
        assert_equal(self.varz.replace_scalar('${n}'), None)

    def test_replace_non_strings_inside_string(self):
        class Example:
            def __str__(self):
                return 'Hello'
        self.varz['${h}'] = Example()
        self.varz['${w}'] = 'world'
        res = self.varz.replace_scalar('Another "${h} ${w}" example')
        assert_equal(res, 'Another "Hello world" example')

    def test_replace_list_item_invalid(self):
        self.varz['@{L}'] = ['v0','v1','v3']
        for inv in ['@{L}[3]', '@{NON}[0]', '@{L[2]}']:
            self.assertRaises(DataError, self.varz.replace_list, [inv])

    def test_replace_non_existing_list(self):
        self.assertRaises(DataError, self.varz.replace_list, ['${nonexisting}'])

    def test_replace_non_existing_scalar(self):
        self.assertRaises(DataError, self.varz.replace_scalar, '${nonexisting}')

    def test_replace_non_existing_string(self):
        self.assertRaises(DataError, self.varz.replace_string, '${nonexisting}')

    def test_replace_escaped(self):
        self.varz['${foo}'] = 'bar'
        for inp, exp in [(r'\${foo}', r'${foo}'),
                         (r'\\${foo}', r'\bar'),
                         (r'\\\${foo}', r'\${foo}'),
                         (r'\\\\${foo}', r'\\bar'),
                         (r'\\\\\${foo}', r'\\${foo}')]:
            assert_equal(self.varz.replace_scalar(inp), exp)

    def test_variables_in_value(self):
        self.varz['${exists}'] = 'Variable exists but is still not replaced'
        self.varz['${test}'] = '${exists} & ${does_not_exist}'
        assert_equal(self.varz['${test}'], '${exists} & ${does_not_exist}')
        self.varz['@{test}'] = ['${exists}', '&', '${does_not_exist}']
        assert_equal(self.varz['@{test}'], '${exists} & ${does_not_exist}'.split())

    def test_variable_as_object(self):
        obj = PythonObject('a', 1)
        self.varz['${obj}'] = obj
        assert_equal(self.varz['${obj}'], obj)
        expected = ['Some text here %s and %s there' % (obj, obj)]
        actual = self.varz.replace_list(['Some text here ${obj} and ${obj} there'])
        assert_equal(actual, expected)

    def test_extended_variables(self):
        # Extended variables are vars like ${obj.name} when we have var ${obj}
        obj = PythonObject('a', [1, 2, 3])
        dic = {'a': 1, 'o': obj}
        self.varz['${obj}'] = obj
        self.varz['${dic}'] = dic
        assert_equal(self.varz.replace_scalar('${obj.a}'), 'a')
        assert_equal(self.varz.replace_scalar('${obj.b}'), [1, 2, 3])
        assert_equal(self.varz.replace_scalar('${obj.b[0]}-${obj.b[1]}'), '1-2')
        assert_equal(self.varz.replace_scalar('${dic["a"]}'), 1)
        assert_equal(self.varz.replace_scalar('${dic["o"]}'), obj)
        assert_equal(self.varz.replace_scalar('-${dic["o"].b[2]}-'), '-3-')

    def test_space_is_not_ignored_after_newline_in_extend_variable_syntax(self):
        self.varz['${x}'] = 'test string'
        self.varz['${lf}'] = '\\n'
        self.varz['${lfs}'] = '\\n '
        for inp, exp in [('${x.replace(" ", """\\n""")}', 'test\nstring'),
                         ('${x.replace(" ", """\\n """)}', 'test\n string'),
                         ('${x.replace(" ", """${lf}""")}', 'test\nstring'),
                         ('${x.replace(" ", """${lfs}""")}', 'test\n string')]:
            assert_equal(self.varz.replace_scalar(inp), exp)

    def test_escaping_with_extended_variable_syntax(self):
        self.varz['${p}'] = 'c:\\temp'
        assert self.varz['${p}'] == 'c:\\temp'
        assert_equal(self.varz.replace_scalar('${p + "\\\\foo.txt"}'),
                     'c:\\temp\\foo.txt')

    def test_internal_variables(self):
        # Internal variables are variables like ${my${name}}
        self.varz['${name}'] = 'name'
        self.varz['${my name}'] = 'value'
        assert_equal(self.varz.replace_scalar('${my${name}}'), 'value')
        self.varz['${whos name}'] = 'my'
        assert_equal(self.varz.replace_scalar('${${whos name} ${name}}'), 'value')
        assert_equal(self.varz.replace_scalar('${${whos${name}}${name}}'), 'value')
        self.varz['${my name}'] = [1, 2, 3]
        assert_equal(self.varz.replace_scalar('${${whos${name}}${name}}'), [1, 2, 3])
        assert_equal(self.varz.replace_scalar('- ${${whos${name}}${name}} -'), '- [1, 2, 3] -')

    def test_math_with_internal_vars(self):
        assert_equal(self.varz.replace_scalar('${${1}+${2}}'), 3)
        assert_equal(self.varz.replace_scalar('${${1}-${2}}'), -1)
        assert_equal(self.varz.replace_scalar('${${1}*${2}}'), 2)
        assert_equal(self.varz.replace_scalar('${${1}//${2}}'), 0)

    def test_math_with_internal_vars_with_spaces(self):
        assert_equal(self.varz.replace_scalar('${${1} + ${2.5}}'), 3.5)
        assert_equal(self.varz.replace_scalar('${${1} - ${2} + 1}'), 0)
        assert_equal(self.varz.replace_scalar('${${1} * ${2} - 1}'), 1)
        assert_equal(self.varz.replace_scalar('${${1} / ${2.0}}'), 0.5)

    def test_math_with_internal_vars_does_not_work_if_first_var_is_float(self):
        assert_raises(DataError, self.varz.replace_scalar, '${${1.1}+${2}}')
        assert_raises(DataError, self.varz.replace_scalar, '${${1.1} - ${2}}')
        assert_raises(DataError, self.varz.replace_scalar, '${${1.1} * ${2}}')
        assert_raises(DataError, self.varz.replace_scalar, '${${1.1}/${2}}')

    def test_list_variable_as_scalar(self):
        self.varz['@{name}'] = exp = ['spam', 'eggs']
        assert_equal(self.varz.replace_scalar('${name}'), exp)
        assert_equal(self.varz.replace_list(['${name}', 42]), [exp, 42])
        assert_equal(self.varz.replace_string('${name}'), str(exp))

    def test_copy(self):
        varz = Variables()
        varz['${foo}'] = 'bar'
        copy = varz.copy()
        assert_equal(copy['${foo}'], 'bar')

    if JYTHON:

        def test_variable_as_object_in_java(self):
            obj = JavaObject('hello')
            self.varz['${obj}'] = obj
            assert_equal(self.varz['${obj}'], obj)
            assert_equal(self.varz.replace_scalar('${obj} world'), 'hello world')

        def test_extended_variables_in_java(self):
            obj = JavaObject('my name')
            self.varz['${obj}'] = obj
            assert_equal(self.varz.replace_list(['${obj.name}']), ['my name'])


if __name__ == '__main__':
    unittest.main()
