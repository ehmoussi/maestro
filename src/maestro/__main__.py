# -*- coding: utf-8 -*-
r"""Makefile of the project."""

import argparse
import inspect
import subprocess as sp
import sys
from pathlib import Path
from typing import Callable, Sequence


def wheel(no_deps: bool = False, wheel_dir: str = ".") -> int:
    r"""Build a wheel of the package."""
    cmd = ["python", "-m", "pip", "wheel"]
    if no_deps:
        cmd += ["--no-deps"]
    cmd += ["--wheel-dir", wheel_dir]
    cmd += ["."]
    return sp.run(cmd).returncode


def ruff(fix: bool = False):
    r"""Run the ruff linter."""
    if sys.version_info >= (3, 7):
        cmd = ["ruff", "check"]
        if fix:
            cmd += ["--fix"]
        cmd += ["src"]
        if Path("tests").exists():
            cmd += ["tests"]
        return sp.run(cmd).returncode
    message = f"Can't run with python {'.'.join(map(str, sys.version_info[:3]))}"
    raise ValueError(message)


def flake8() -> int:
    r"""Run the flake8 linter."""
    return sp.run(["flake8", "src", "tests"]).returncode


def mypy() -> int:
    r"""Run the mypy typer."""
    cmd = ["mypy", "--config-file"]
    if sys.version_info >= (3, 7):
        cmd += ["pyproject.toml"]
    else:
        cmd += ["mypy.ini"]
    cmd += ["--pretty"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return sp.run(cmd).returncode


def black() -> int:
    r"""Apply black."""
    cmd = ["black"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return sp.run(cmd).returncode


def black_check() -> int:
    r"""Check if black has been applied."""
    cmd = ["black", "--check"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return sp.run(cmd).returncode


def isort() -> int:
    r"""Apply isort."""
    cmd = ["isort"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return sp.run(cmd).returncode


def isort_check() -> int:
    r"""Check if isort has been applied."""
    cmd = ["isort", "--check"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return sp.run(cmd).returncode


def linting() -> int:
    r"""Apply black and isort, and check the linting with ruff/flake8 and mypy."""
    if sys.version_info >= (3, 7):
        linting_functions = (black, isort, ruff, mypy)
    else:
        linting_functions = (black, isort, flake8, mypy)
    return_code = _running_multiple_functions(linting_functions)
    if return_code == 0:
        print("Everything is ok !")  # noqa: T201
    else:
        print("Oops !")  # noqa: T201
    return return_code


def test(name: str) -> int:
    r"""Run the given test."""
    return sp.run(["pytest", "-vv", name]).returncode


def tests() -> int:
    r"""Run the tests."""
    return sp.run(
        [
            "pytest",
            "-vv",
            "-n",
            "auto",
            "--dist",
            "loadfile",
            "tests",
        ]
    ).returncode


def tests_failed() -> int:
    r"""Run the last failed tests."""
    return sp.run(["pytest", "-vv", "--lf", "tests"]).returncode


def tests_cov(xml: bool = False, html: bool = False) -> int:
    r"""Run the tests with coverage."""
    cmd = [
        "pytest",
        "-n",
        "auto",
        "--dist",
        "loadfile",
    ]
    if xml:
        cmd += ["--cov-report=xml", "--junitxml=report.xml"]
    if html:
        cmd += ["--cov-report=html"]
    cmd += ["--cov=src", "--cov-report=term-missing:skip-covered", "-vv", "tests"]
    return_code = sp.run(cmd).returncode
    if return_code == 0 and xml:
        return_code = sp.run(["python", "-m", "coverage", "xml"]).returncode
    return return_code


def icons(package_name: str) -> int:
    r"""Generate the icons.py file."""
    if not Path("src", package_name).exists():
        raise ValueError(f"'{package_name}' is not in the 'src' folder")
    return sp.run(
        [
            "pyrcc5",
            # "-name",
            # "initialize",
            f"src/{package_name}/icons/icons.qrc",
            "-o",
            f"src/{package_name}/icons/icons.py",
        ]
    ).returncode


def _running_multiple_functions(
    functions: Sequence[Callable[..., int]], with_print: bool = True, **kwargs
) -> int:
    for f in functions:
        if with_print:
            print(f"Running {f.__name__} ...")  # noqa: T201
        return_code = f(**kwargs)
        if return_code != 0:
            if with_print:
                print(f"{f.__name__} failed ...")  # noqa: T201
            return return_code
        if with_print:
            print(f"{f.__name__} done ...")  # noqa: T201
    return 0


def _get_functions():
    return [
        obj
        for name, obj in inspect.getmembers(sys.modules[__name__])
        if inspect.isfunction(obj) and not name.startswith("_") and name != "main"
    ]


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parsers_functions = {}
    for f in _get_functions():
        parser_function = subparsers.add_parser(f.__name__, help=f.__doc__)
        parser_function.set_defaults(func=f)
        f_signature = inspect.signature(f)
        for var_name, var_value in f_signature.parameters.items():
            options = {}
            if var_value.default is not inspect._empty:  # noqa: SLF001
                options = {"default": var_value.default}
            if var_value.annotation is bool:
                options["action"] = "store_true"
            else:
                options["type"] = var_value.annotation
            parser_function.add_argument(f"--{var_name.replace('_', '-')}", **options)
        parsers_functions[f.__name__] = parser_function
    # parsing
    args = parser.parse_args()
    func_kwargs = {
        keyword: getattr(args, keyword)
        for keyword in dir(args)
        if (
            not keyword.startswith("_")
            and keyword != "func"
            and getattr(args, keyword) is not inspect._empty  # noqa: SLF001
        )
    }
    if hasattr(args, "func"):
        return args.func(**func_kwargs)
    else:
        parser.print_help()


if __name__ == "__main__":
    sys.exit(main())
