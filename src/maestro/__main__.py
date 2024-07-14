"""Commands of maestro."""

import subprocess as sp
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.prompt import Prompt
from rich.table import Column
from typing_extensions import Annotated

CONSOLE = Console()
app = typer.Typer(
    no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]}
)


def run_command(cmd: List[str]) -> int:
    process = sp.run(
        cmd, stdout=CONSOLE.file, stderr=CONSOLE.file, text=True, encoding="utf-8"
    )
    return process.returncode


def find_packages_in_src() -> List[str]:
    packages = []
    for p in Path("src").iterdir():
        if p.is_dir() and Path(p, "__init__.py").exists():
            packages.append(p.name)
    return packages


@app.command()
def ruff(fix: bool = False) -> int:
    r"""Run the ruff linter."""
    if sys.version_info >= (3, 7):
        cmd = ["ruff", "check"]
        if fix:
            cmd += ["--fix"]
        cmd += ["src"]
        if Path("tests").exists():
            cmd += ["tests"]
        return run_command(cmd)
    else:
        message = f"Can't run with python {'.'.join(map(str, sys.version_info[:3]))}"
        raise ValueError(message)


@app.command()
def flake8() -> int:
    r"""Run the flake8 linter."""
    cmd = ["flake8", "src", "tests"]
    return run_command(cmd)


typer.Argument()


@app.command()
def mypy(
    config_file: Annotated[Optional[Path], typer.Option("--config_file", "-c")] = None,
) -> int:
    r"""Run the mypy typer."""
    cmd = ["mypy", "--config-file"]
    if config_file is None:
        if sys.version_info >= (3, 7):
            cmd += ["pyproject.toml"]
        else:
            cmd += ["mypy.ini"]
    else:
        cmd += [str(config_file)]
    cmd += ["--pretty"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return run_command(cmd)


@app.command()
def black(check: bool = False) -> int:
    r"""Apply black."""
    cmd = ["black"]
    if check:
        cmd += ["--check"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return run_command(cmd)


@app.command()
def isort(check: bool = False) -> int:
    r"""Apply isort."""
    cmd = ["isort"]
    if check:
        cmd += ["--check"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    return run_command(cmd)


@app.command()
def linting() -> int:
    r"""Apply black and isort, check linting with ruff and the type with mypy."""
    return_code = 0
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, table_column=Column(ratio=2)),
        auto_refresh=False,
    ) as progress:
        task = progress.add_task(description="Linting", total=4)
        if sys.version_info >= (3, 7):
            linting_functions = (black, isort, ruff, mypy)
        else:
            linting_functions = (black, isort, flake8, mypy)
        for f in linting_functions:
            progress.update(task, description=f"{f.__name__} start", refresh=True)
            return_code = f()  # type: ignore[operator]
            if return_code == 0:
                progress.update(task, description=f"{f.__name__} Ok", advance=1, refresh=True)
            else:
                progress.update(task, description=f"{f.__name__} failed", refresh=True)
                break
        if return_code == 0:
            progress.update(task, description="Linting Ok", refresh=True)
    return return_code


@app.command()
def test(
    file_or_dir: Annotated[Optional[List[str]], typer.Argument()] = None,
    parallel: bool = False,
    failed: bool = False,
    coverage: bool = False,
    xml: bool = False,
    html: bool = False,
) -> int:
    r"""Run the tests."""
    cmd = ["pytest", "-vv"]
    if parallel:
        cmd += ["-n", "auto", "--dist", "loadfile"]
    if failed:
        cmd += ["--lf"]
    if coverage:
        cmd += ["--cov=src", "--cov-report=term-missing:skip-covered"]
        if xml:
            cmd += ["--cov-report=xml", "--junitxml=report.xml"]
        if html:
            cmd += ["--cov-report=html"]
    if file_or_dir is None:
        cmd += ["tests"]
    else:
        cmd += file_or_dir
    return run_command(cmd)


@app.command()
def wheel(wheel_dir: Path, all_deps: bool = False) -> int:
    r"""Build a wheel of the package."""
    if not wheel_dir.exists():
        wheel_dir.mkdir()
    if not wheel_dir.is_dir():
        raise ValueError(f"{wheel_dir} is not a directory")
    if wheel_dir.absolute() == Path.cwd() and all_deps:
        typer.confirm(
            "All the wheels of the dependencies will be created in the current directory. "
            "Are you sure ?",
            abort=True,
        )
    cmd = ["python", "-m", "pip", "wheel"]
    if not all_deps:
        cmd += ["--no-deps"]
    cmd += ["--wheel-dir", str(wheel_dir)]
    cmd += ["."]
    return run_command(cmd)


@app.command()
def icons() -> int:
    r"""Generate the icons.py file from the qrc file."""
    packages = find_packages_in_src()
    package_name = Prompt.ask("Select a package", choices=packages, default=packages[0])
    qrc_file = Path("src", package_name, "icons", "icons.qrc")
    if not qrc_file.exists():
        CONSOLE.print(f"'{qrc_file}' doesn't exists")
        qrc_file_str = Prompt.ask("Enter the qrc file path")
        qrc_file = Path(qrc_file_str)
    if not qrc_file.is_file():
        raise ValueError(f"'{qrc_file}' is not a file.")
    if not qrc_file.exists():
        raise ValueError(f"'{qrc_file}' doesn't exists. Can't generate the 'icons.py' file.")
    py_file = Path(qrc_file.parent, "icons.py")
    return sp.run(
        [
            "pyrcc5",
            # "-name",
            # "initialize",
            qrc_file,
            "-o",
            py_file,
        ]
    ).returncode
