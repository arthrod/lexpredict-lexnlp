"""Common routines for testing NLP functions against test data stored
separately in CSV files.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import csv
import inspect
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import psutil
from memory_profiler import memory_usage

from lexnlp.extract.common.base_path import lexnlp_test_path

DIR_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DIR_BENCHMARKS = os.path.join(DIR_ROOT, "benchmarks")
FN_BENCHMARKS = os.path.join(DIR_BENCHMARKS, "benchmarks.csv")
FN_PROBLEMS = os.path.join(DIR_BENCHMARKS, "problems_hr.txt")
DIR_TEST_DATA = os.path.join(DIR_ROOT, "test_data")
IN_CELL_CSV_DELIMITER = "|"
IN_CELL_CSV_NONE = ""
SYS_OS_UNAME = os.uname()
try:
    SYS_CPU_FREQ = psutil.cpu_freq()
except FileNotFoundError:
    SYS_CPU_FREQ = None
SYS_CPU_FREQ = SYS_CPU_FREQ.current if SYS_CPU_FREQ else None
SYS_CPU_COUNT = psutil.cpu_count()
SYS_MEM_TOTAL = psutil.virtual_memory().total
SYS_OS_NAME = f"{SYS_OS_UNAME.sysname} {SYS_OS_UNAME.release} ({SYS_OS_UNAME.version})"
SYS_NODE_NAME = SYS_OS_UNAME.nodename
SYS_ARCH = SYS_OS_UNAME.machine


def this_test_data_path(create_dirs: bool = False, caller_stack_offset: int = 1):
    """
    Compute the CSV test-data path corresponding to the calling test function.

    Parameters:
        create_dirs (bool): If true, create the containing directories if they do not exist.
        caller_stack_offset (int): Stack-frame offset to locate the caller; use 1 when called directly from the test function and increase by 1 for each intermediate wrapper.

    Returns:
        str: Filesystem path to the CSV file for the calling test function (under the configured test data directory).
    """
    stack = inspect.stack()
    module_name = inspect.getmodule(stack[caller_stack_offset][0]).__name__
    file_dir = os.path.normpath(os.path.join(DIR_TEST_DATA, *module_name.split(".")))
    if create_dirs:
        os.makedirs(file_dir, exist_ok=True)
    file_name = os.path.join(file_dir, stack[caller_stack_offset][3] + ".csv")
    return file_name


def iter_test_data_text_and_tuple(file_name: str | None = None, call_stack_offset: int = 0):
    """
    Iterate test cases from a CSV file, yielding a sequence of (row_index, text, input_args, expected_values).

    CSV conventions:
    - The first column is treated as the test text; subsequent rows may leave this cell empty to add further expected values for the previous text.
    - Header columns starting with `input_` are collected into `input_args`; their names are normalized by removing the `input_` prefix and any trailing `_bool`, `_int`, or `_str` suffix.
    - Remaining header columns (except the first) are treated as expected output columns.
    - Empty cells are treated as `None`.
    - Rows whose text cell starts with `###` are skipped.

    Value conversion rules (based on column name suffix):
    - Columns ending with `_bool` convert "true"/"false" (case-insensitive) to `bool`.
    - Columns ending with `_int` convert to `int`.
    - Columns ending with `_str` (or columns with no recognized suffix) remain as `str`.
    - Cells that are empty become `None`.

    Parameters:
        file_name (str | None): Path to the CSV file to read. If `None`, the caller's test-data path is computed automatically.
        call_stack_offset (int): Additional stack offset to use when computing the automatic test-data path.

    Yields:
        tuple: (row_index, text, input_args, expected_values_list)
            - row_index (int): zero-based index of the CSV row most recently read for this text block.
            - text (str): the test text for this block.
            - input_args (dict): mapping of normalized input argument names to their converted values.
            - expected_values_list (list): list of expected values for the text; each item is `None`, a single value, or a tuple of values depending on the number of expected output columns.
    """
    if not file_name:
        file_name = this_test_data_path(create_dirs=False, caller_stack_offset=2 + call_stack_offset)
    print(f"\n\nLoading test data:\n{file_name}\n")

    with open(file_name, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        input_columns = [col for col in reader.fieldnames if col.startswith("input_")]
        expected_output_columns = [col for col in reader.fieldnames[1:] if col not in input_columns]
        cur_text = None
        cur_input_args = None
        cur_expected_value_list = []
        i = -1

        def input_arg(column_name: str) -> str:
            if column_name.startswith("input_"):
                column_name = column_name[len("input_") :]
            if column_name.endswith("_bool"):
                column_name = column_name[: -len("_bool")]
            elif column_name.endswith("_int"):
                column_name = column_name[: -len("_int")]
            elif column_name.endswith("_str"):
                column_name = column_name[: -len("_str")]
            return column_name

        def read_value(column_name: str, value_str: str) -> Any:
            if not value_str:
                return None
            if column_name.endswith("_bool"):
                return value_str.lower() == "true"
            if column_name.endswith("_int"):
                return int(value_str)
            return value_str

        for line in reader:
            i = i + 1

            # Empty strings are Nones
            for field_name in reader.fieldnames:
                if not line.get(field_name):
                    line[field_name] = None

            text = line.get(reader.fieldnames[0])

            if text and text.startswith("###"):
                continue

            if text:
                # if it is not the first found text
                if cur_text:
                    yield i, cur_text, cur_input_args, cur_expected_value_list

                cur_expected_value_list = []
                cur_text = text
                cur_input_args = {input_arg(key): read_value(key, line.get(key)) for key in input_columns}

            if not cur_text:
                continue

            expected_value_tuple_or_string = tuple(read_value(key, line.get(key)) for key in expected_output_columns)
            if all(item is None for item in expected_value_tuple_or_string):
                expected_value_tuple_or_string = None
            elif len(expected_value_tuple_or_string) == 1:
                expected_value_tuple_or_string = expected_value_tuple_or_string[0]

            if expected_value_tuple_or_string:
                cur_expected_value_list.append(expected_value_tuple_or_string)

        if cur_text:
            yield i, cur_text, cur_input_args, cur_expected_value_list


def write_test_data_text_and_tuple(texts: tuple, values: tuple, column_names: tuple):
    """
    Writes test data to external file for further using in tests.
    File name is calculated by this_test_data_path(..) function (test_data/pack/a/ge/test_file_name/test_method_name).
    Test data is written in CSV format with the special rules to allow multiple expected value tuples per single text.
    Header: Text,Component 1 Title,...,Component N Title
            Text 1,Value Component 1.1 of Text 1,...,Value Component 1.N of Text 1
            ,Value Component 2.1 of Text 1,...,Value Component 2.N of Text 1
            ...
            ,Value Component M.1 of Text 1,...,Value Component M.N of Text 1
            Text 2,Value Component 1.1 of Text 2,...,Value Component 1.N of Text 2
            ,Value Component 2.1 of Text 2,...,Value Component 2.N of Text 2
            ...
            ,Value Component K.1 of Text 2,...,Value Component K.N of Text 2
            ...
    So if there is no text in the first column in a row - this means to match the values to the last filled text above.

    :param texts: Tuple of text stirngs ("texts" column).
    :param values: Tuple of expected values matching texts on the same index (expected values column(s))
    :param column_names: Names of the columns. Should be: Text, Name of First Entry in Values, Name of Second Entry...
    :return:
    """

    file_name = this_test_data_path(create_dirs=True, caller_stack_offset=2)
    with open(file_name, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        for i, text in enumerate(texts):
            multiple_values = values[i]
            first = True
            if not multiple_values:
                writer.writerow((text,))
            else:
                for values_tuple_or_string in multiple_values:
                    if first:
                        first = False
                    else:
                        text = None
                    if isinstance(values_tuple_or_string, (tuple, list)):
                        row = [text]
                        for v in values_tuple_or_string:
                            row.append(v)
                        row = tuple(row)
                    else:
                        row = (text, values_tuple_or_string)
                    writer.writerow(row)
    return file_name


def build_extraction_func_name(func: Callable, **kwargs):
    kwargs_str = ""
    if kwargs:
        kwargs_list = list()
        for key, value in kwargs.items():
            str_value = str(value)
            if len(str_value) < 50:
                value = "'" + value + "'" if isinstance(value, str) else str(value)
            elif isinstance(value, list):
                value = "list(" + str(len(value)) + " el.)"
            elif isinstance(value, tuple):
                value = "tuple(" + str(len(value)) + " el.)"
            elif isinstance(value, set):
                value = "set(" + str(len(value)) + " el.)"
            elif isinstance(value, dict):
                value = "dict(" + str(len(value)) + " el.)"
            else:
                value = str(type(value))
            kwargs_list.append(key + "=" + value)

        kwargs_str = ", ".join(kwargs_list)
    return func.__name__ + "(text" + ((", " + kwargs_str) if kwargs_str else "") + ")"


def test_extraction_func_on_test_data(
    func: Callable,
    benchmark_name: str | None = None,
    expected_data_converter: Callable = None,
    actual_data_converter: Callable = None,
    test_only_expected_in: bool = False,
    debug_print: bool = False,
    start_from_csv_line: int | None = None,
    test_data_path: str | None = None,
    **kwargs,
):
    """
    Run an extraction function against test cases loaded from a CSV file and assert results match expected values.

    Loads test data (by default from the path computed by this_test_data_path) and, for each text block, calls the provided extraction function and compares the produced results to the expected values from the CSV. Collects all failures and raises an AssertionError summarizing problems after processing all cases.

    Parameters:
      func: The extraction function to test.
      benchmark_name (str | None): Optional explicit name used for benchmarking and in failure messages; generated from `func` when omitted.
      expected_data_converter (Callable | None): Optional transformer applied to expected values read from the CSV before comparison.
      actual_data_converter (Callable | None): Optional transformer applied to the function's result before comparison.
      test_only_expected_in (bool): If true, assert that each expected value is contained within the actual results rather than requiring exact equality.
      debug_print (bool): If true, print actual and expected results for each passing case.
      start_from_csv_line (int | None): If set, skip CSV rows before this 1-based line number.
      test_data_path (str | None): Optional explicit CSV file path to use instead of the computed test-data path.
      **kwargs: Additional keyword arguments forwarded to the extraction function (and used when building the benchmark name).

    Raises:
      FileNotFoundError: If `test_data_path` is provided but the file cannot be found.
      AssertionError: If any test cases fail; the raised message references FN_PROBLEMS where detailed failure logs are written.
    """
    if not benchmark_name:
        benchmark_name = build_extraction_func_name(func, **kwargs)

    problems = []

    if test_data_path:
        file_name = test_data_path
        if not os.path.isfile(file_name):
            file_name = os.path.join(lexnlp_test_path, file_name)
        if not os.path.isfile(file_name):
            raise FileNotFoundError(f'File "{test_data_path}" was not found')
    else:
        file_name = this_test_data_path(create_dirs=False, caller_stack_offset=2)

    for i, text, input_args, expected in iter_test_data_text_and_tuple(file_name):
        if start_from_csv_line and i < start_from_csv_line - 1:
            continue
        kwargs.update(input_args)
        actual, expected, problem = test_extraction_func(
            expected,
            func,
            text,
            benchmark_name=benchmark_name,
            test_data_file=file_name,
            expected_data_converter=expected_data_converter,
            actual_data_converter=actual_data_converter,
            do_raise=False,
            test_only_expected_in=test_only_expected_in,
            **kwargs,
        )
        if problem:
            problems.append(f"{i + 1}) {problem}")
            print(problem)
        elif debug_print:
            print(
                "================================================================================================\n"
                f"Actual:\n{fmt_results(actual)}\n\n"
                f"Expected:\n{fmt_results(expected)}\n"
                "================================================================================================\n"
            )

    if problems:
        raise AssertionError(f"Testing NLP function {benchmark_name} failed. See log for problems:\n{FN_PROBLEMS}")


def test_extraction_func(
    expected,
    func: Callable,
    text,
    benchmark_name: str | None = None,
    test_data_file: str | None = None,
    expected_data_converter: Callable = None,
    actual_data_converter: Callable = None,
    do_raise: bool = True,
    debug_print: bool = False,
    test_only_expected_in: bool = False,
    **kwargs,
):
    """
    Run an extraction function on a text, compare its output to the expected value(s), and return the observed result, the shaped expected value, and an optional problem message.

    Parameters:
        expected: Expected value(s) for the text; may be a single value, a sequence, or None. If `expected_data_converter` is provided it will be applied; if `test_only_expected_in` is True and no converter is provided, `expected` is reduced to its first element or `None` when empty.
        func (Callable): Extraction function to call with `text` and `**kwargs`.
        text (str): Input text passed to `func`.
        benchmark_name (str | None): Optional name used for benchmarking and reporting; derived from `func` and `kwargs` when omitted.
        test_data_file (str | None): Optional path included in failure messages to identify the source CSV.
        expected_data_converter (Callable | None): Function to transform `expected` before comparison.
        actual_data_converter (Callable | None): Function to transform the raw result returned by `func` before comparison.
        do_raise (bool): If True, assertion helpers will raise on mismatch; otherwise they return a formatted problem string.
        debug_print (bool): When True, include additional debug output in equality assertions.
        test_only_expected_in (bool): If True, assert that the single expected value is contained in the actual results (membership); otherwise require set equality.
        **kwargs: Additional keyword arguments forwarded to `func` and used when deriving the benchmark name.

    Returns:
        tuple:
            actual: Observed result after optional conversion; converted to a `set` when truthy, otherwise `None`.
            expected: Expected value after optional conversion and shaping; converted to a `set` when truthy (unless `test_only_expected_in` was applied), otherwise `None`.
            problem (str | None): Formatted failure message when an assertion fails, or `None` when the test passed.
    """
    if not benchmark_name:
        benchmark_name = build_extraction_func_name(func, **kwargs)

    if expected_data_converter:
        expected = expected_data_converter(expected)
    elif test_only_expected_in:
        expected = expected[0] if expected else None

    actual = benchmark(benchmark_name, func, text, **kwargs)
    if actual_data_converter:
        actual = actual_data_converter(actual)
    actual = set(actual) if actual else None

    if test_only_expected_in:
        problem = assert_in(benchmark_name, text, expected, actual, do_raise=do_raise, test_data_file=test_data_file)
    else:
        expected = set(expected) if expected else None
        problem = assert_set_equal(
            benchmark_name,
            text,
            actual,
            expected,
            do_raise=do_raise,
            test_data_file=test_data_file,
            debug_print=debug_print,
        )

    return actual, expected, problem


def benchmark_extraction_func(func: Callable, text, **kwargs):
    benchmark_name = build_extraction_func_name(func, **kwargs)
    return benchmark(benchmark_name, func, text, **kwargs)


def benchmark_decorator(function, *args, **kwargs):
    def wrapper():
        benchmark_name = f"{function.__name__}(args={args} kwargs={kwargs})"
        res = benchmark(benchmark_name, function, *args, **kwargs)
        return res

    return wrapper


def benchmark(benchmark_name: str, func: Callable, *args, benchmark_file: str = FN_BENCHMARKS, **kwargs):
    ts = time.time()
    # ``memory_profiler.memory_usage`` spawns a subprocess to sample RSS. In
    # sandboxed CI runners (no ``fork``, restricted ``/proc``, etc.) that
    # subprocess can deadlock on ``parent_conn.recv()`` — the test suite then
    # hangs until the pytest-timeout watchdog fires. Allow opting out via
    # ``LEXNLP_DISABLE_MEMORY_PROFILER=1`` (default: enabled on CI because
    # GitHub Actions sets ``CI=true``) and fall back to a plain function call
    # so the benchmark step reports zero MB instead of hanging the suite.
    use_memory_profiler = not (os.environ.get("LEXNLP_DISABLE_MEMORY_PROFILER") or os.environ.get("CI"))
    if use_memory_profiler:
        try:
            mem_res = memory_usage((func, args, kwargs), max_usage=True, retval=True)
        except Exception:  # pragma: no cover — fork/permission failures
            use_memory_profiler = False
    if not use_memory_profiler:
        mem_res = (0.0, func(*args, **kwargs))
    exec_time = time.time() - ts
    res = mem_res[1]
    print(mem_res)
    max_memory_usage = mem_res[0] if isinstance(mem_res[0], (float, int)) else mem_res[0][0]

    benchmark_dir = os.path.dirname(benchmark_file)
    os.makedirs(benchmark_dir, exist_ok=True)
    exists = os.path.isfile(benchmark_file) and os.stat(benchmark_file).st_size
    with open(benchmark_file, "a" if exists else "w", encoding="utf8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(
                (
                    "date",
                    "function",
                    "text_size_chars",
                    "exec_time_sec",
                    "max_memory_usage_mb",
                    "sys_cpu_count",
                    "sys_cpu_freq",
                    "sys_ram_total",
                    "sys_os",
                    "sys_node_name",
                    "sys_arch",
                )
            )

        text = args[0] if len(args) > 0 and isinstance(args[0], str) else "None"
        text_size = len(text) if text else 0
        writer.writerow(
            (
                datetime.now(UTC).isoformat(),
                benchmark_name,
                text_size,
                exec_time,
                max_memory_usage,
                SYS_CPU_COUNT,
                SYS_CPU_FREQ,
                SYS_MEM_TOTAL,
                SYS_OS_NAME,
                SYS_NODE_NAME,
                SYS_ARCH,
            )
        )
        print(
            f"{benchmark_name}\n{fmt_short_text(text, 100)}\nText size: {text_size:5d}, Exec Time (s): {exec_time:4.4f}, Max Memory (mb): {max_memory_usage:4.4f}\n"
        )

    return res


def assert_set_equal(
    function_name: str,
    text: str,
    actual_results: set,
    expected_results: set,
    problems_file: str = FN_PROBLEMS,
    do_raise: bool = True,
    do_write_to_file: bool = True,
    debug_print: bool = True,
    test_data_file: str | None = None,
) -> str | None:
    """
    Report and optionally record a detailed problem when the actual and expected result sets differ.

    When the sets are equal (including both empty), no action is taken and the function returns None. If they differ, a human-readable problem message describing the input text, the actual results, and the expected results is produced; depending on flags the message is appended to `problems_file`, printed to stdout, and/or an AssertionError is re-raised.

    Parameters:
       function_name (str): Name of the function under test (used in the problem message).
       text (str): The input text that produced the results (included in the problem message).
       actual_results (set): Result set produced by the function.
       expected_results (set): Expected result set to compare against.
       problems_file (str): Path to the file where the problem message will be appended when `do_write_to_file` is True.
       do_raise (bool): If True, re-raise the captured AssertionError after reporting the problem.
       do_write_to_file (bool): If True, append the problem message to `problems_file`.
       debug_print (bool): If True, print the problem message to stdout.
       test_data_file (str | None): Optional path to the test data CSV; when provided its relative path is included in the problem message.

    Returns:
       str | None: The formatted problem message when a mismatch is found, or `None` when the sets are equal.

    Raises:
       AssertionError: Re-raised when a mismatch is detected and `do_raise` is True.
    """
    if not expected_results and not actual_results:
        return None
    exx = None
    try:
        assert actual_results == expected_results
    except AssertionError as ex:
        exx = ex

    if exx:
        title = f'Function {function_name} returns wrong results on "{fmt_short_text(text)}"'
        body = """
-----------------------------------------------------------------------------------------------------------------------
{data_file_note}*Problem:*
Try executing NLP function *{function_name}* on text:
{{code}}
{text}
{{code}}


It returns (actual result):
{{code}}
{actual}
{{code}}


But it should return (expected result):
{{code}}
{expected}
{{code}}


*Desired Outcome:*
Check the function.
If the expected data is correct then fix the function. Otherwise, fix the expected data.
=======================================================================================================================
        """.format(
            function_name=function_name,
            text=text,
            actual=fmt_results(actual_results),
            expected=fmt_results(expected_results),
            data_file_note=f"Test data file: {os.path.relpath(test_data_file, DIR_ROOT)}\n\n" if test_data_file else "",
        )
        problem = title + body

        if do_write_to_file:
            with open(problems_file, "a", encoding="utf8") as f:
                f.write(problem)
                f.write("\n\n")

        if debug_print:
            print(problem)

        if do_raise:
            raise exx or AssertionError()
        return problem


def fmt_short_text(text: str, max_len: int = 40):
    orig_len = len(text)
    text = text[:max_len]
    text = text.replace("\t", " ")
    text = text.replace("\n", " ")
    while "  " in text:
        text = text.replace("  ", " ")
    if orig_len > max_len:
        text = text + "..."
    return text


def fmt_results(results: set | list | tuple):
    return "\n".join([str(r) for r in results]) if results else ""


def assert_in(
    function_name: str,
    text: str,
    expected_in,
    actual_results: set,
    problems_file: str = FN_PROBLEMS,
    do_raise: bool = True,
    do_write_to_file: bool = True,
    test_data_file: str | None = None,
) -> str | None:
    """
    Assert that `expected_in` is contained within `actual_results`; on failure, produce a formatted problem message and optionally write it to a problems file or raise.

    Parameters:
        function_name (str): Name of the tested function to include in the problem message.
        text (str): Source text used to produce `actual_results`; a short preview is included in the message.
        expected_in: The element expected to be present in `actual_results`.
        actual_results (set): The set of results produced by the function under test.
        problems_file (str): File path to append the formatted problem report when a failure occurs.
        do_raise (bool): If True, raise an AssertionError on failure; if False, return the formatted problem message.
        do_write_to_file (bool): If True, append the problem message to `problems_file` when a failure occurs.
        test_data_file (str | None): Optional test-data CSV path to reference in the problem message.

    Returns:
        str | None: The formatted problem message when the assertion fails and `do_raise` is False; `None` when the assertion succeeds.

    Raises:
        AssertionError: When the assertion fails and `do_raise` is True.
    """
    exx = None
    try:
        assert expected_in in actual_results
    except AssertionError as ex:
        exx = ex

    if exx:
        title = f'Function {function_name} returns wrong results on "{fmt_short_text(text)}"'
        body = """
-----------------------------------------------------------------------------------------------------------------------
{data_file_note}*Problem:*
Try executing NLP function *{function_name}* on text:
{{code}}
{text}
{{code}}


It returns (actual result):
{{code}}
{actual}
{{code}}


But its results should also contain:
{{code}}
{expected_in}
{{code}}


*Desired Outcome:*
Check the function.
If the expected data is correct then fix the function. Otherwise, fix the expected data.
=======================================================================================================================
        """.format(
            function_name=function_name,
            text=text,
            actual=fmt_results(actual_results),
            expected_in=expected_in,
            data_file_note=f"Test data file: {os.path.relpath(test_data_file, DIR_ROOT)}\n\n" if test_data_file else "",
        )
        problem = title + body

        if do_write_to_file:
            with open(problems_file, "a", encoding="utf8") as f:
                f.write(problem)
                f.write("\n\n")

        if do_raise:
            raise exx or AssertionError()
        return problem
