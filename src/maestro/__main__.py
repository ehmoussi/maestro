"""Commands of maestro."""

from maestro import pyprojecttoml

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.prompt import Prompt
from rich.table import Column
from typing_extensions import Annotated

import itertools
import subprocess as sp
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional

CONSOLE = Console()
app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(pyprojecttoml.app, name="pyproject")


def run_command(cmd: List[str], with_exit: bool = True) -> int:
    if sys.version_info >= (3, 7):  # noqa: UP036
        process = sp.run(
            cmd,
            check=False,
            stdout=CONSOLE.file,
            stderr=CONSOLE.file,
            text=True,
            encoding="utf-8",
        )
    else:
        process = sp.run(
            cmd,
            check=False,
            stdout=CONSOLE.file,
            stderr=CONSOLE.file,
            universal_newlines=True,  # noqa: UP021
            encoding="utf-8",
        )
    return_code = process.returncode
    if with_exit and return_code != 0:
        raise typer.Exit(return_code)
    else:
        return return_code


def find_packages_in_src() -> List[str]:
    return [
        p.name for p in Path("src").iterdir() if p.is_dir() and Path(p, "__init__.py").exists()
    ]


@app.command()
def ruff(
    fix: bool = False,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help="Replace the default config file",
        ),
    ] = None,
    show_config: Annotated[
        Optional[bool],
        typer.Option("--show-config", "-s"),
    ] = False,
) -> int:
    """Run the ruff linter."""
    if sys.version_info >= (3, 7):  # noqa: UP036
        default_config = Path("pyproject.toml")
        cmd = ["ruff", "check"]
        if config is None:
            config = default_config
        if config.exists():
            cmd += ["--config", str(config)]
        else:
            msg = f"The file {config} doesn't exist"
            raise ValueError(msg)
        if fix:
            cmd += ["--fix"]
        cmd += ["src"]
        if Path("tests").exists():
            cmd += ["tests"]
        if show_config:
            CONSOLE.print(default_config.read_text())
            return 0
        else:
            return run_command(cmd)
    else:
        message = f"Can't run with python {'.'.join(map(str, sys.version_info[:3]))}"
        raise ValueError(message)


@app.command()
def flake8(
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help="Replace the default config file",
        ),
    ] = None,
    append_config: Annotated[
        Optional[Path],
        typer.Option(
            "--append-config",
            "-a",
            help="Append the default config file",
        ),
    ] = None,
    show_default_config: Annotated[
        Optional[bool],
        typer.Option("--show-default-config", "-d"),
    ] = False,
) -> int:
    r"""Run the flake8 linter."""
    default_config = Path(Path(__file__).parent, "cfg", "flake8")
    if show_default_config:
        CONSOLE.print(default_config.read_text())
        return 0
    if config is None:
        config = default_config
    if config.exists():
        cmd = ["flake8", "--config", str(config)]
    else:
        msg = f"The file {config} doesn't exist"
        raise ValueError(msg)
    if append_config is None:
        append_config = Path("setup.cfg")
    if append_config.exists():
        cmd += ["--append-config", str(append_config)]
    else:
        msg = f"The file {append_config} doesn't exist"
        raise ValueError(msg)
    cmd += ["src", "tests"]
    return run_command(cmd)


@app.command()
def mypy(
    config_file: Annotated[
        Optional[Path],
        typer.Option("--config_file", "-c"),
    ] = None,
    strict: Annotated[
        Optional[bool],
        typer.Option("--strict", "-s"),
    ] = None,
    pyqt5: Annotated[
        Optional[bool], typer.Option("--pyqt5", help="Set to true use PyQt5 from QtPy")
    ] = True,
    pyqt6: Annotated[
        Optional[bool], typer.Option("--pyqt6", help="Set to true the use PyQt6 from QtPy")
    ] = False,
    pyside2: Annotated[
        Optional[bool], typer.Option("--pyside2", help="Set to true the use PySide2 from QtPy")
    ] = False,
    pyside6: Annotated[
        Optional[bool], typer.Option("--pyside6", help="Set to true the use PySide6 from QtPy")
    ] = False,
    file_or_dir: Annotated[
        Optional[List[str]],
        typer.Argument(help="Path to a file or directory"),
    ] = None,
) -> int:
    r"""Run the mypy typer."""
    cmd = ["mypy", "--config-file"]
    if config_file is None:
        if sys.version_info >= (3, 7):  # noqa: UP036
            config_file = Path("pyproject.toml")
        else:
            config_file = Path("mypy.ini")
    if not config_file.exists():
        msg = f"The file {config_file} doesn't exist"
        raise ValueError(msg)
    cmd += [str(config_file)]
    cmd += ["--pretty", "--warn-unused-configs"]
    if strict is not None:
        cmd += ["--strict"]
    if pyqt6:
        cmd += [
            "--always-false=PYQT5",
            "--always-true=PYQT6",
            "--always-false=PYSIDE2",
            "--always-false=PYSIDE6",
        ]
    elif pyside2:
        cmd += [
            "--always-false=PYQT5",
            "--always-false=PYQT6",
            "--always-true=PYSIDE2",
            "--always-false=PYSIDE6",
        ]
    elif pyside6:
        cmd += [
            "--always-false=PYQT5",
            "--always-false=PYQT6",
            "--always-false=PYSIDE2",
            "--always-true=PYSIDE6",
        ]
    else:
        cmd += [
            "--always-true=PYQT5",
            "--always-false=PYQT6",
            "--always-false=PYSIDE2",
            "--always-false=PYSIDE6",
        ]
    if file_or_dir is None:
        if Path("src").exists():
            cmd += ["src"]
        else:
            raise ValueError("No 'src' folder found.")
        if next(Path("tests").glob("**/*.py"), None) is not None:
            cmd += ["tests"]
    else:
        for f in file_or_dir:
            cmd += [f]
    return run_command(cmd)


@app.command()
def black(
    check: bool = False,
    line_length: Annotated[
        Optional[int],
        typer.Option("--line_length", "-l"),
    ] = 95,
) -> int:
    r"""Apply black."""
    cmd = ["black", "-l", str(line_length)]
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
def isort(
    check: bool = False,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help="Replace the default config file",
        ),
    ] = None,
    show_config: Annotated[
        Optional[bool],
        typer.Option("--show-config", "-s"),
    ] = False,
) -> int:
    r"""Apply isort."""
    default_config = Path("pyproject.toml")
    if config is None:
        config = default_config
    if config.exists():
        cmd = ["isort", "--settings-file", str(config)]
    else:
        msg = f"The file {config} doesn't exist"
        raise ValueError(msg)
    if check:
        cmd += ["--check"]
    if Path("src").exists():
        cmd += ["src"]
    else:
        raise ValueError("No 'src' folder found.")
    if Path("tests").exists():
        cmd += ["tests"]
    if show_config:
        CONSOLE.print(default_config.read_text())
        return 0
    else:
        return_code = run_command(cmd, with_exit=False)
        if return_code == 0:
            CONSOLE.print("Isort done.")
        else:
            raise typer.Exit(return_code)
        return return_code


@app.command()
def linting() -> int:
    """Apply black, isort, linting with ruff and check types with mypy."""
    return_code = 0
    with Progress(
        TextColumn(
            "[progress.description]{task.description} ({task.completed} of {task.total})"
        ),
        BarColumn(bar_width=None, table_column=Column(ratio=2)),
        auto_refresh=False,
    ) as progress:
        task = progress.add_task(description="Linting", total=4)
        if sys.version_info >= (3, 7):  # noqa: UP036
            linting_functions = (black, isort, ruff, mypy)
        else:
            linting_functions = (black, isort, flake8, mypy)
        for f in linting_functions:
            progress.update(task, description=f"{f.__name__} start")
            try:
                return_code = f()
            except typer.Exit as e:
                return_code = e.exit_code
            if return_code == 0:
                progress.update(task, description=f"{f.__name__} Ok")
                progress.advance(task)
            else:
                progress.update(task, description=f"{f.__name__} failed")
                break
            progress.refresh()
        if return_code == 0:
            progress.update(task, description="Linting Ok")
            progress.refresh()
    if return_code == 0:
        CONSOLE.print(":party_popper: Nice! :party_popper:", emoji=True)
    else:
        CONSOLE.print(":loudly_crying_face: Oh no!! :loudly_crying_face:", emoji=True)
        raise typer.Exit(return_code)
    return return_code


class CoverageReport(Enum):
    XML = "xml"
    HTML = "html"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    def __format__(self, _: str) -> str:
        return self.value


@app.command()
def test(
    file_or_dir: Annotated[
        Optional[List[str]],
        typer.Argument(help="Path to the test file or directory"),
    ] = None,
    parallel: Annotated[
        bool,
        typer.Option(
            "--parallel",
            "-p",
            help="Run in parallel grouped by file",
        ),
    ] = False,
    only_failed: Annotated[
        bool,
        typer.Option(
            "--only-failed",
            "-lf",
            help="Run only the tests that failed at the last run",
        ),
    ] = False,
    coverage: Annotated[
        bool,
        typer.Option("--coverage", "--cov", help="Add coverage"),
    ] = False,
    coverage_report: Annotated[
        Optional[List[CoverageReport]],
        typer.Option(
            "--coverage-report",
            "--cov-report",
            help="Add coverage and generate an xml or/and html report",
        ),
    ] = None,
    coverage_only: Annotated[
        Optional[List[Path]],
        typer.Option(
            "--coverage-only",
            "--cov-only",
            help="Add coverage only for the given files",
        ),
    ] = None,
) -> int:
    r"""Run the tests."""
    cmd = ["pytest", "-vv"]
    if parallel:
        cmd += ["-n", "auto", "--dist", "loadfile"]
    if only_failed:
        cmd += ["--lf"]
    if coverage or coverage_report is not None or coverage_only is not None:
        if coverage or coverage_report is not None:
            cmd += ["--cov=src", "--cov-report=term-missing:skip-covered"]
        elif coverage_only is not None:
            for cov_filepath in coverage_only:
                if cov_filepath.is_file():
                    cov_python_import = (
                        str(Path(*cov_filepath.parts[1:]))
                        .replace("//", ".")
                        .replace("\\\\", ".")
                        .replace("/", ".")
                        .replace("\\", ".")
                        .replace(".py", "")
                    )
                    cmd += [f"--cov={cov_python_import}"]
                else:
                    cmd += [f"--cov={cov_filepath}"]
            cmd += ["--cov-report=term-missing:skip-covered"]
        if coverage_report is not None:
            if "xml" in map(str, coverage_report):
                cmd += ["--cov-report=xml", "--junitxml=report.xml"]
            if "html" in map(str, coverage_report):
                cmd += ["--cov-report=html"]
    if file_or_dir is None:
        cmd += ["tests"]
    else:
        cmd += file_or_dir
    return run_command(cmd)


@app.command()
def wheel(
    wheel_dir: Annotated[
        Path,
        typer.Argument(
            ...,
            metavar="DIR",
            help="Build wheel(s) into DIR",
        ),
    ],
    all_deps: Annotated[
        bool,
        typer.Option(
            "--all-deps",
            "--all",
            help="Build wheel of the package dependencies",
        ),
    ] = False,
) -> int:
    r"""Build a wheel of the package."""
    if not wheel_dir.exists():
        wheel_dir.mkdir()
    if not wheel_dir.is_dir():
        msg = f"{wheel_dir} is not a directory"
        raise ValueError(msg)
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


class QtAPI(Enum):
    PYQT5 = "pyqt5"
    PYSIDE6 = "pyside6"


@app.command()
def icons(
    qt_api: Annotated[
        QtAPI,
        typer.Option(
            "--qt",
            help="Specify the Qt binding version. By default PyQt5 is used",
        ),
    ] = QtAPI.PYQT5,
) -> int:
    """Generate the icons.py file from the qrc file."""
    packages = find_packages_in_src()
    package_name = Prompt.ask("Select a package", choices=packages, default=packages[0])
    qrc_file = Path("src", package_name, "icons", "icons.qrc")
    if not qrc_file.exists():
        CONSOLE.print(f"'{qrc_file}' doesn't exists")
        qrc_file_str = Prompt.ask("Enter the qrc file path")
        qrc_file = Path(qrc_file_str)
    if not qrc_file.is_file():
        msg = f"'{qrc_file}' is not a file."
        raise ValueError(msg)
    if not qrc_file.exists():
        msg = f"'{qrc_file}' doesn't exists. Can't generate the 'icons.py' file."
        raise ValueError(msg)
    py_file = Path(qrc_file.parent, "icons.py")
    pyrcc_command = "pyrcc5"
    if qt_api == QtAPI.PYSIDE6:
        pyrcc_command = "pyside6-rcc"
    return run_command(
        [
            pyrcc_command,
            # "-name",
            # "initialize",
            str(qrc_file),
            "-o",
            str(py_file),
        ]
    )


@app.command()
def vscode(
    forced: Annotated[
        bool, typer.Option("--forced", "-f", help="Replace all the files")
    ] = False
) -> int:
    """Generate the settings for VS Code."""
    maestro_cfg_path = Path(Path(__file__).parent, "cfg")
    maestro_vscode_path = Path(Path(__file__).parent, "vscode")
    vscode_path = Path(Path.cwd(), ".vscode")
    for maestro_file in itertools.chain(
        maestro_vscode_path.iterdir(), maestro_cfg_path.iterdir()
    ):
        if maestro_file.stem == "flake8":
            continue
        vscode_file = Path(vscode_path, maestro_file.name)
        can_replace = True
        display_path = f"{vscode_path.name}/{vscode_file.name}"
        if not forced and vscode_file.exists():
            can_replace = typer.confirm(
                f"The file '{display_path}' alredy exists.\nDo you want to replace it ?"
            )
        if can_replace:
            vscode_file.write_text(maestro_file.read_text())
            CONSOLE.print(f"[green italic]'{display_path}' has been replaced.")
        else:
            CONSOLE.print(f"[red italic]'{display_path}' has not been replaced.")
    return 0


@app.command()
def gitlab(
    forced: Annotated[
        bool, typer.Option("--forced", "-f", help="Replace all the files")
    ] = False
) -> int:
    """Generate the templates for Gitlab."""
    maestro_gitlab_path = Path(Path(__file__).parent, "gitlab")
    gitlab_path = Path(Path.cwd(), ".gitlab")
    for maestro_gitlab_subfolder in Path(maestro_gitlab_path).iterdir():
        gitlab_subfolder = Path(gitlab_path, maestro_gitlab_subfolder.name)
        for maestro_gitlab_file in maestro_gitlab_subfolder.iterdir():
            gitlab_file = Path(gitlab_subfolder, maestro_gitlab_file.name)
            can_write = True
            display_path = f".gitlab/{gitlab_subfolder.name}/{gitlab_file.name}"
            if not forced and gitlab_file.exists():
                can_write = typer.confirm(
                    f"The file '{display_path}' alredy exists.\nDo you want to replace it ?"
                )
            if not gitlab_file.parent.exists():
                gitlab_file.parent.mkdir(parents=True, exist_ok=True)
            if can_write:
                is_new = not gitlab_file.exists()
                gitlab_file.write_text(maestro_gitlab_file.read_text())
                if is_new:
                    CONSOLE.print(f"[green italic]'{display_path}' has been created.")
                else:
                    CONSOLE.print(f"[green italic]'{display_path}' has been replaced.")
            else:
                CONSOLE.print(f"[red italic]'{display_path}' has not been replaced.")
    return 0


def version_callback(has_version: bool) -> None:
    if has_version:
        if sys.version_info >= (3, 8):
            from importlib.metadata import version as get_version
        else:
            from importlib_metadata import version as get_version

        CONSOLE.print(get_version("maestro"))
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Get the version", callback=version_callback),
    ] = False
) -> None: ...


if __name__ == "__main__":
    app(prog_name="maestro")
