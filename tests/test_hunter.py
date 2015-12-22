from __future__ import print_function

import inspect
import os
import platform
import subprocess
import sys
import tokenize

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
try:
    from itertools import izip_longest
except ImportError:
    from itertools import zip_longest as izip_longest

import pytest

import hunter
from hunter import And
from hunter import Not
from hunter import Or
from hunter import Q
from hunter import Query
from hunter import stop
from hunter import trace
from hunter import When

from hunter import CodePrinter
from hunter import Debugger
from hunter import VarsPrinter

pytest_plugins = 'pytester',


@pytest.yield_fixture(autouse=True, scope="function")
def auto_stop():
    try:
        yield
    finally:
        stop()


def _get_func_spec(func):
    spec = inspect.getargspec(func)
    return inspect.formatargspec(spec.args, spec.varargs)


def test_pth_activation():
    module_name = os.path.__name__
    expected_module = "{0}.py".format(module_name)
    hunter_env = "module={!r},function=\"join\"".format(module_name)
    func_spec = _get_func_spec(os.path.join)
    expected_call = "call      def join{0}:".format(func_spec)

    output = subprocess.check_output(
        [sys.executable, os.path.join(os.path.dirname(__file__), 'sample.py')],
        env=dict(os.environ, PYTHONHUNTER=hunter_env),
        stderr=subprocess.STDOUT,
    )
    assert expected_module.encode() in output
    assert expected_call.encode() in output


def test_pth_sample4():
    env = dict(os.environ, PYTHONHUNTER="CodePrinter")
    env.pop('COVERAGE_PROCESS_START', None)
    env.pop('COV_CORE_SOURCE', None)
    output = subprocess.check_output(
        [sys.executable, os.path.join(os.path.dirname(__file__), 'sample4.py')],
        env=env,
        stderr=subprocess.STDOUT,
    )
    assert output


def test_pth_sample2(LineMatcher):
    env = dict(os.environ, PYTHONHUNTER="module='__main__'")
    env.pop('COVERAGE_PROCESS_START', None)
    env.pop('COV_CORE_SOURCE', None)
    output = subprocess.check_output(
        [sys.executable, os.path.join(os.path.dirname(__file__), 'sample2.py')],
        env=env,
        stderr=subprocess.STDOUT,
    )
    lm = LineMatcher(output.decode('utf-8').splitlines())
    lm.fnmatch_lines([
        '*tests*sample2.py:* call      if __name__ == "__main__":  #*',
        '*tests*sample2.py:* line      if __name__ == "__main__":  #*',
        '*tests*sample2.py:* line          import functools',
        '*tests*sample2.py:* line          def deco(opt):',
        '*tests*sample2.py:* line          @deco(1)',
        '*tests*sample2.py:* call          def deco(opt):',
        '*tests*sample2.py:* line              def decorator(func):',
        '*tests*sample2.py:* line              return decorator',
        '*tests*sample2.py:* return            return decorator',
        '*                 * ...       return value: <function deco*',
        '*tests*sample2.py:* line          @deco(2)',
        '*tests*sample2.py:* call          def deco(opt):',
        '*tests*sample2.py:* line              def decorator(func):',
        '*tests*sample2.py:* line              return decorator',
        '*tests*sample2.py:* return            return decorator',
        '*                 * ...       return value: <function deco*',
        '*tests*sample2.py:* line          @deco(3)',
        '*tests*sample2.py:* call          def deco(opt):',
        '*tests*sample2.py:* line              def decorator(func):',
        '*tests*sample2.py:* line              return decorator',
        '*tests*sample2.py:* return            return decorator',
        '*                 * ...       return value: <function deco*',
        '*tests*sample2.py:* call              def decorator(func):',
        '*tests*sample2.py:* line                  @functools.wraps(func)',
        '*tests*sample2.py:* line                  return wrapper',
        '*tests*sample2.py:* return                return wrapper',
        '*                 * ...       return value: <function foo *',
        '*tests*sample2.py:* call              def decorator(func):',
        '*tests*sample2.py:* line                  @functools.wraps(func)',
        '*tests*sample2.py:* line                  return wrapper',
        '*tests*sample2.py:* return                return wrapper',
        '*                 * ...       return value: <function foo *',
        '*tests*sample2.py:* call              def decorator(func):',
        '*tests*sample2.py:* line                  @functools.wraps(func)',
        '*tests*sample2.py:* line                  return wrapper',
        '*tests*sample2.py:* return                return wrapper',
        '*                 * ...       return value: <function foo *',
        '*tests*sample2.py:* line          foo(',
        "*tests*sample2.py:* line              'a*',",
        "*tests*sample2.py:* line              'b'",
        '*tests*sample2.py:* call                  @functools.wraps(func)',
        '*                 *    |                  def wrapper(*args):',
        '*tests*sample2.py:* line                      return func(*args)',
        '*tests*sample2.py:* call                  @functools.wraps(func)',
        '*                 *    |                  def wrapper(*args):',
        '*tests*sample2.py:* line                      return func(*args)',
        '*tests*sample2.py:* call                  @functools.wraps(func)',
        '*                 *    |                  def wrapper(*args):',
        '*tests*sample2.py:* line                      return func(*args)',
        '*tests*sample2.py:* call          @deco(1)',
        '*                 *    |          @deco(2)',
        '*                 *    |          @deco(3)',
        '*                 *    |          def foo(*args):',
        '*tests*sample2.py:* line              return args',
        '*tests*sample2.py:* return            return args',
        "*                 * ...       return value: ('a*', 'b')",
        "*tests*sample2.py:* return                    return func(*args)",
        "*                 * ...       return value: ('a*', 'b')",
        "*tests*sample2.py:* return                    return func(*args)",
        "*                 * ...       return value: ('a*', 'b')",
        "*tests*sample2.py:* return                    return func(*args)",
        "*                 * ...       return value: ('a*', 'b')",
        "*tests*sample2.py:* line          try:",
        "*tests*sample2.py:* line              None(",
        "*tests*sample2.py:* line                  'a',",
        "*tests*sample2.py:* line                  'b'",
        "*tests*sample2.py:* exception             'b'",
        "*                 * ...       exception value: *",
        "*tests*sample2.py:* line          except:",
        "*tests*sample2.py:* line              pass",
        "*tests*sample2.py:* return            pass",
        "*                   ...       return value: None",
    ])


def test_predicate_str_repr():
    assert repr(Q(module='a')).endswith("predicates.Query: query_eq={'module': 'a'}>")
    assert str(Q(module='a')) == "Query(module='a')"

    assert "predicates.When: condition=<hunter." in repr(Q(module='a', action='foo'))
    assert "predicates.Query: query_eq={'module': 'a'}>, actions=['foo']>" in repr(Q(module='a', action='foo'))
    assert str(Q(module='a', action='foo')) == "When(Query(module='a'), 'foo')"

    assert "predicates.Not: predicate=<hunter." in repr(~Q(module='a'))
    assert "predicates.Query: query_eq={'module': 'a'}>>" in repr(~Q(module='a'))
    assert str(~Q(module='a')) == "Not(Query(module='a'))"

    assert "predicates.Or: predicates=(<hunter." in repr(Q(module='a') | Q(module='b'))
    assert "predicates.Query: query_eq={'module': 'a'}>, " in repr(Q(module='a') | Q(module='b'))
    assert repr(Q(module='a') | Q(module='b')).endswith("predicates.Query: query_eq={'module': 'b'}>)>")
    assert str(Q(module='a') | Q(module='b')) == "Or(Query(module='a'), Query(module='b'))"

    assert "predicates.And: predicates=(<hunter." in repr(Q(module='a') & Q(module='b'))
    assert "predicates.Query: query_eq={'module': 'a'}>," in repr(Q(module='a') & Q(module='b'))
    assert repr(Q(module='a') & Q(module='b')).endswith("predicates.Query: query_eq={'module': 'b'}>)>")
    assert str(Q(module='a') & Q(module='b')) == "And(Query(module='a'), Query(module='b'))"


def test_predicate_q_nest_1():
    assert repr(Q(Q(module='a'))).endswith("predicates.Query: query_eq={'module': 'a'}>")


def test_predicate_q_expansion():
    assert Q(1, 2, module=3) == Or(1, 2, Q(module=3))
    assert Q(1, 2, module=3, action=4) == When(Or(1, 2, Q(module=3)), 4)
    assert Q(1, 2, module=3, actions=[4, 5]) == When(Or(1, 2, Q(module=3)), 4, 5)


def test_predicate_and():
    assert And(1, 2) == And(1, 2)
    assert Q(module=1) & Q(module=2) == And(Q(module=1), Q(module=2))
    assert Q(module=1) & Q(module=2) & Q(module=3) == And(Q(module=1), Q(module=2), Q(module=3))

    assert (Q(module=1) & Q(module=2))({'module': 3}) == False
    assert (Q(module=1) & Q(function=2))({'module': 1, 'function': 2}) == True

    assert And(1, 2) | 3 == Or(And(1, 2), 3)


def test_predicate_or():
    assert Q(module=1) | Q(module=2) == Or(Q(module=1), Q(module=2))
    assert Q(module=1) | Q(module=2) | Q(module=3) == Or(Q(module=1), Q(module=2), Q(module=3))

    assert (Q(module=1) | Q(module=2))({'module': 3}) == False
    assert (Q(module=1) | Q(module=2))({'module': 2}) == True

    assert Or(1, 2) & 3 == And(Or(1, 2), 3)


def test_tracing_bare(LineMatcher):
    lines = StringIO()
    with trace(CodePrinter(stream=lines)):
        def a():
            return 1

        b = a()
        b = 2
        try:
            raise Exception("BOOM!")
        except Exception:
            pass
    print(lines.getvalue())
    lm = LineMatcher(lines.getvalue().splitlines())
    lm.fnmatch_lines([
        "* ...       return value: <hunter.*tracer.Tracer *",
        "*test_hunter.py* call              def a():",
        "*test_hunter.py* line                  return 1",
        "*test_hunter.py* return                return 1",
        "* ...       return value: 1",
    ])


def test_tracing_printing_failures(LineMatcher):
    lines = StringIO()
    with trace(CodePrinter(stream=lines), VarsPrinter("x", stream=lines)):
        class Bad(Exception):
            def __repr__(self):
                raise RuntimeError("I'm a bad class!")

        def a():
            x = Bad()
            return x

        def b():
            x = Bad()
            raise x

        a()
        try:
            b()
        except Exception as exc:
            pass
    lm = LineMatcher(lines.getvalue().splitlines())
    lm.fnmatch_lines([
        """* ...       return value: <hunter.*tracer.Tracer *""",
        """*tests*test_hunter.py:* call              class Bad(Exception):""",
        """*tests*test_hunter.py:* line              class Bad(Exception):""",
        """*tests*test_hunter.py:* line                  def __repr__(self):""",
        """*tests*test_hunter.py:* return                def __repr__(self):""",
        """* ...       return value: *""",
        """*tests*test_hunter.py:* call              def a():""",
        """*tests*test_hunter.py:* line                  x = Bad()""",
        """*tests*test_hunter.py:* line                  return x""",
        """* vars      x => !!! FAILED REPR: RuntimeError("I'm a bad class!",)""",
        """*tests*test_hunter.py:* return                return x""",
        """* ...       return value: !!! FAILED REPR: RuntimeError("I'm a bad class!",)""",
        """* vars      x => !!! FAILED REPR: RuntimeError("I'm a bad class!",)""",
        """*tests*test_hunter.py:* call              def b():""",
        """*tests*test_hunter.py:* line                  x = Bad()""",
        """*tests*test_hunter.py:* line                  raise x""",
        """* vars      x => !!! FAILED REPR: RuntimeError("I'm a bad class!",)""",
        """*tests*test_hunter.py:* exception             raise x""",
        """* ...       exception value: !!! FAILED REPR: RuntimeError("I'm a bad class!",)""",
        """* vars      x => !!! FAILED REPR: RuntimeError("I'm a bad class!",)""",
        """*tests*test_hunter.py:* return                raise x""",
        """* ...       return value: None""",
        """* vars      x => !!! FAILED REPR: RuntimeError("I'm a bad class!",)""",
    ])


def test_tracing_vars(LineMatcher):
    lines = StringIO()
    with trace(actions=[VarsPrinter('b', stream=lines), CodePrinter(stream=lines)]):
        def a():
            b = 1
            b = 2
            return 1

        b = a()
        b = 2
        try:
            raise Exception("BOOM!")
        except Exception:
            pass
    print(lines.getvalue())
    lm = LineMatcher(lines.getvalue().splitlines())
    lm.fnmatch_lines([
        "* ...       return value: <hunter.*tracer.Tracer *",
        "*test_hunter.py* call              def a():",
        "*test_hunter.py* line                  b = 1",
        "* vars      b => 1",
        "*test_hunter.py* line                  b = 2",
        "* vars      b => 2",
        "*test_hunter.py* line                  return 1",
        "* vars      b => 2",
        "*test_hunter.py* return                return 1",
        "* ...       return value: 1",
    ])


def test_trace_merge():
    trace(function="a")
    trace(function="b")
    assert trace(function="c")._handler == When(Q(function="c"), CodePrinter)


def test_trace_api_expansion():
    # simple use
    with trace(function="foobar") as t:
        assert t._handler == When(Q(function="foobar"), CodePrinter)

    # "or" by expression
    with trace(module="foo", function="foobar") as t:
        assert t._handler == When(Q(module="foo", function="foobar"), CodePrinter)

    # pdb.set_trace
    with trace(function="foobar", action=Debugger) as t:
        assert t._handler == When(Q(function="foobar"), Debugger)

    # pdb.set_trace on any hits
    with trace(module="foo", function="foobar", action=Debugger) as t:
        assert t._handler == When(Q(module="foo", function="foobar"), Debugger)

    # pdb.set_trace when function is foobar, otherwise just print when module is foo
    with trace(Q(function="foobar", action=Debugger), module="foo") as t:
        assert t._handler == When(Or(
            When(Q(function="foobar"), Debugger),
            Q(module="foo")
        ), CodePrinter)

    # dumping variables from stack
    with trace(Q(function="foobar", action=VarsPrinter("foobar")), module="foo") as t:
        assert t._handler == When(Or(
            When(Q(function="foobar"), VarsPrinter("foobar")),
            Q(module="foo"),
        ), CodePrinter)

    with trace(Q(function="foobar", action=VarsPrinter("foobar", "mumbojumbo")), module="foo") as t:
        assert t._handler == When(Or(
            When(Q(function="foobar"), VarsPrinter("foobar", "mumbojumbo")),
            Q(module="foo"),
        ), CodePrinter)

    # multiple actions
    with trace(Q(function="foobar", actions=[VarsPrinter("foobar"), Debugger]), module="foo") as t:
        assert t._handler == When(Or(
            When(Q(function="foobar"), VarsPrinter("foobar"), Debugger),
            Q(module="foo"),
        ), CodePrinter)

    # customization
    assert trace(lambda event: event.locals.get("node") == "Foobar",
                 module="foo", function="foobar")
    assert trace(Q(lambda event: event.locals.get("node") == "Foobar",
                   function="foobar", actions=[VarsPrinter("foobar"), Debugger]), module="foo", )
    assert trace(Q(function="foobar", actions=[VarsPrinter("foobar"),
                                               lambda event: print("some custom output")]), module="foo", )


def test_trace_with_class_actions():
    with trace(CodePrinter):
        def a():
            pass

        a()


def test_predicate_no_inf_recursion():
    assert Or(And(1)) == 1
    assert Or(Or(1)) == 1
    assert And(Or(1)) == 1
    assert And(And(1)) == 1
    predicate = Q(Q(lambda ev: 1, module='wat'))
    print('predicate:', predicate)
    predicate('foo')


def test_predicate_compression():
    assert Or(Or(1, 2), And(3)) == Or(1, 2, 3)
    assert Or(Or(1, 2), 3) == Or(1, 2, 3)
    assert Or(1, Or(2, 3), 4) == Or(1, 2, 3, 4)
    assert And(1, 2, Or(3, 4)).predicates == (1, 2, Or(3, 4))

    assert repr(Or(Or(1, 2), And(3))) == repr(Or(1, 2, 3))
    assert repr(Or(Or(1, 2), 3)) == repr(Or(1, 2, 3))
    assert repr(Or(1, Or(2, 3), 4)) == repr(Or(1, 2, 3, 4))


def test_predicate_not():
    assert Not(1).predicate == 1
    assert ~Or(1, 2) == Not(Or(1, 2))
    assert ~And(1, 2) == Not(And(1, 2))

    assert ~Not(1) == 1

    assert ~Query(module=1) | ~Query(module=2) == Not(And(Query(module=1), Query(module=2)))
    assert ~Query(module=1) & ~Query(module=2) == Not(Or(Query(module=1), Query(module=2)))

    assert ~Query(module=1) | Query(module=2) == Or(Not(Query(module=1)), Query(module=2))
    assert ~Query(module=1) & Query(module=2) == And(Not(Query(module=1)), Query(module=2))

    assert ~(Query(module=1) & Query(module=2)) == Not(And(Query(module=1), Query(module=2)))
    assert ~(Query(module=1) | Query(module=2)) == Not(Or(Query(module=1), Query(module=2)))

    assert repr(~Or(1, 2)) == repr(Not(Or(1, 2)))
    assert repr(~And(1, 2)) == repr(Not(And(1, 2)))

    assert repr(~Query(module=1) | ~Query(module=2)) == repr(Not(And(Query(module=1), Query(module=2))))
    assert repr(~Query(module=1) & ~Query(module=2)) == repr(Not(Or(Query(module=1), Query(module=2))))

    assert repr(~(Query(module=1) & Query(module=2))) == repr(Not(And(Query(module=1), Query(module=2))))
    assert repr(~(Query(module=1) | Query(module=2))) == repr(Not(Or(Query(module=1), Query(module=2))))

    assert Not(Q(module=1))({'module': 1}) == False


def test_predicate_query_allowed():
    pytest.raises(TypeError, Query, 1)
    pytest.raises(TypeError, Query, a=1)


def test_predicate_when_allowed():
    pytest.raises(TypeError, When, 1)


@pytest.mark.parametrize('expr,inp,expected', [
    ({'module': "abc"}, {'module': "abc"}, True),
    ({'module': "abcd"}, {'module': "abc"}, False),
    ({'module': "abcd"}, {'module': "abce"}, False),
    ({'module_startswith': "abc"}, {'module': "abcd"}, True),
    ({'module__startswith': "abc"}, {'module': "abcd"}, True),
    ({'module_contains': "bc"}, {'module': "abcd"}, True),

    ({'module_endswith': "abc"}, {'module': "abcd"}, False),
    ({'module__endswith': "bcd"}, {'module': "abcd"}, True),

    ({'module_in': "abcd"}, {'module': "bc"}, True),
    ({'module': "abcd"}, {'module': "bc"}, False),
    ({'module': ["abcd"]}, {'module': "bc"}, False),
    ({'module_in': ["abcd"]}, {'module': "bc"}, False),
    ({'module_in': ["a", "bc", "d"]}, {'module': "bc"}, True),

    ({'module': "abcd"}, {'module': "abc"}, False),

    ({'module_startswith': ("abc", "xyz")}, {'module': "abc"}, True),
    ({'module_startswith': {"abc", "xyz"}}, {'module': "abc"}, True),
    ({'module_startswith': ["abc", "xyz"]}, {'module': "abc"}, True),
    ({'module_startswith': ("abc", "xyz")}, {'module': "abcd"}, True),

    ({'module_startswith': ("abc", "xyz")}, {'module': "xyzw"}, True),
    ({'module_startswith': ("abc", "xyz")}, {'module': "fooabc"}, False),

    ({'module': "abc"}, {'module': 1}, False),

    ({'module_regex': r"(re|sre.*)\b"}, {'module': "regex"}, False),
    ({'module_regex': r"(re|sre.*)\b"}, {'module': "re.gex"}, True),
    ({'module_regex': r"(re|sre.*)\b"}, {'module': "sregex"}, True),
    ({'module_regex': r"(re|sre.*)\b"}, {'module': "re"}, True),
])
def test_predicate_matching(expr, inp, expected):
    assert Query(**expr)(inp) == expected


@pytest.mark.parametrize('exc_type,expr', [
    (TypeError, {'module_1': 1}),
    (TypeError, {'module1': 1}),
    (ValueError, {'module_startswith': 1}),
    (ValueError, {'module_startswith': {1: 2}}),
    (ValueError, {'module_endswith': 1}),
    (ValueError, {'module_endswith': {1: 2}}),
    (TypeError, {'module_foo': 1}),
])
def test_predicate_bad_query(expr, exc_type):
    pytest.raises(exc_type, Query, **expr)


def test_predicate_when():
    called = []
    assert When(Q(module=1), lambda ev: called.append(ev))({'module': 2}) == False
    assert called == []

    assert When(Q(module=1), lambda ev: called.append(ev))({'module': 1}) == True
    assert called == [{'module': 1}]

    called = []
    assert Q(module=1, action=lambda ev: called.append(ev))({'module': 1}) == True
    assert called == [{'module': 1}]

    called = [[], []]
    predicate = (
        Q(module=1, action=lambda ev: called[0].append(ev)) |
        Q(module=2, action=lambda ev: called[1].append(ev))
    )
    assert predicate({'module': 1}) == True
    assert called == [[{'module': 1}], []]

    assert predicate({'module': 2}) == True
    assert called == [[{'module': 1}], [{'module': 2}]]

    called = [[], []]
    predicate = (
        Q(module=1, action=lambda ev: called[0].append(ev)) &
        Q(function=2, action=lambda ev: called[1].append(ev))
    )
    assert predicate({'module': 2}) == False
    assert called == [[], []]

    assert predicate({'module': 1, 'function': 2}) == True
    assert called == [[{'module': 1, 'function': 2}], [{'module': 1, 'function': 2}]]


def test_proper_backend():
    if os.environ.get('PUREPYTHONHUNTER') or platform.python_implementation() == 'PyPy':
        assert 'hunter.tracer.Tracer' in repr(hunter.Tracer)
    else:
        assert 'hunter._tracer.Tracer' in repr(hunter.Tracer)


@pytest.fixture(scope="session", params=['pure', 'cython'])
def tracer_impl(request):
    if request.param == 'pure':
        return pytest.importorskip('hunter.tracer').Tracer
    elif request.param == 'cython':
        return pytest.importorskip('hunter._tracer').Tracer


def _tokenize():
    with open(tokenize.__file__, 'rb') as fh:
        toks = []
        try:
            for tok in tokenize.tokenize(fh.readline):
                toks.append(tok)
        except tokenize.TokenError as exc:
            toks.append(exc)


def test_perf_filter(tracer_impl, benchmark):
    t = tracer_impl()

    @benchmark
    def run():
        with t.trace(Q(module="does-not-exist") | Q(module="does not exist".split())):
            _tokenize()


def test_perf_actions(tracer_impl, benchmark):
    t = tracer_impl()

    @benchmark
    def run():
        output = StringIO()
        with t.trace(Q(
            ~Q(module_in=['re', 'sre', 'sre_parse']) & ~Q(module_startswith='namedtuple') & Q(kind="call"),
            actions=[
                CodePrinter(
                    stream=output
                ),
                VarsPrinter(
                    'line',
                    globals=True,
                    stream=output
                )
            ]
        )):
            _tokenize()
