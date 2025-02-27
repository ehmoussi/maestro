"""Tool to modify the pyproject.toml file."""

import toml
import typer
from typing_extensions import Annotated

from pathlib import Path

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Add the configuration of the linter libraries to the pyproject.toml file.",
)


@app.command()
def ruff(
    forced: Annotated[
        bool, typer.Option("--forced", "-f", help="Replace all the files")
    ] = False,
    parent_dir: Path = Path(),
) -> None:
    pyproject_filepath = Path(parent_dir, "pyproject.toml")
    if not pyproject_filepath.exists():
        raise ValueError("The file 'pyproject.toml' doesn't exists.")
    pyproject_toml = toml.load(pyproject_filepath)
    if "tool" not in pyproject_toml:
        pyproject_toml["tool"] = {}
    if not forced and "ruff" in pyproject_toml["tool"]:
        if "target-version" in pyproject_toml["tool"]["ruff"]:
            raise ValueError(
                "'target-version' in 'tool.ruff' is already configured. "
                "Add -f to overwrite the existing configuration."
            )
        if "line-length" in pyproject_toml["tool"]["ruff"]:
            raise ValueError(
                "'line-length' in 'tool.ruff' is already configured. "
                "Add -f to overwrite the existing configuration."
            )
    elif "ruff" not in pyproject_toml["tool"]:
        pyproject_toml["tool"]["ruff"] = {}
    pyproject_toml["tool"]["ruff"]["target-version"] = "py37"
    pyproject_toml["tool"]["ruff"]["line-length"] = 95
    if not forced and "lint" in pyproject_toml["tool"]["ruff"]:
        if "select" in pyproject_toml["tool"]["ruff"]["lint"]:
            raise ValueError(
                "'select' in 'tool.ruff.lint' is already configured. "
                "Add -f to overwrite the existing configuration."
            )
        if "ignore" in pyproject_toml["tool"]["ruff"]["lint"]:
            raise ValueError(
                "'ignore' in 'tool.ruff.lint' is already configured. "
                "Add -f to overwrite the existing configuration."
            )
    elif "lint" not in pyproject_toml["tool"]["ruff"]:
        pyproject_toml["tool"]["ruff"]["lint"] = {}
    pyproject_toml["tool"]["ruff"]["lint"]["select"] = [
        "F",
        "E",
        "W",
        # "I",
        "N",
        "UP",
        "YTT",
        "ANN",
        # "S",
        "BLE",
        # "FBT",
        "B",
        "A",
        "COM",
        # "CPY",
        "C4",
        # "DTZ",
        "T10",
        "EM",
        "EXE",
        # "FA",
        "ISC",
        "ICN",
        "LOG",
        "G",
        "INP",
        "PIE",
        "T20",
        "PYI",
        "PT",
        "Q",
        "RSE",
        "RET",
        "SLOT",
        "SLF",
        "SIM",
        "TID",
        "TCH",
        "INT",
        "ARG",
        "PTH",
        "TD",
        # "FIX",
        # "ERA",
        "PD",
        "PGH",
        "PL",
        "TRY",
        "FLY",
        "NPY",
        "PERF",
        "FURB",
        "RUF",
    ]
    pyproject_toml["tool"]["ruff"]["lint"]["ignore"] = [
        "ANN401",  # useful for salome or qt objects
        "ARG001",  # useful to keep the same signature for the slot functions
        "ARG002",  # if you inherit a method the unused args are necessary
        "COM812",  # TODO: Remove ?
        "EM101",  # TODO: Remove !
        "PD011",  # False-positive all over the place
        "PLC1901",  # bad rule x = "" --> replace x == "" with not x
        "PLR0911",  # bad rule multiple return can be better
        "PLR0912",
        "PLR0913",
        "PLR0915",
        "PLR2004",
        "PTH123",
        "RET501",
        "RET505",
        "RET506",
        "SIM108",
        "SIM116",
        "TD002",
        "TD003",
        "TC001",
        "TC002",
        "TC003",
        "TRY002",
        "TRY003",
        "UP006",
        "UP007",
    ]
    with open(pyproject_filepath, "w") as f:
        toml.dump(pyproject_toml, f)


@app.command()
def isort(
    forced: Annotated[
        bool, typer.Option("--forced", "-f", help="Replace all the files")
    ] = False,
    parent_dir: Path = Path(),
) -> None:
    pyproject_filepath = Path(parent_dir, "pyproject.toml")
    if not pyproject_filepath.exists():
        raise ValueError("The file 'pyproject.toml' doesn't exists.")
    pyproject_toml = toml.load(pyproject_filepath)
    if "tool" not in pyproject_toml:
        pyproject_toml["tool"] = {}
    if not forced and "isort" in pyproject_toml["tool"]:
        raise ValueError(
            "tool.isort is already configured. "
            "Add -f to overwrite the existing configuration."
        )
    else:
        pyproject_toml["tool"]["isort"] = {
            "sections": "LOCALFOLDER,FIRSTPARTY,THIRDPARTY,STDLIB,FUTURE",
            "multi_line_output": 3,
            "line_length": 95,
            "use_parentheses": True,
            "include_trailing_comma": True,
            "force_grid_wrap": 0,
            "ensure_newline_before_comments": True,
        }
    with open(pyproject_filepath, "w") as f:
        toml.dump(pyproject_toml, f)


@app.command()
def mypy(
    parent_dir: Path = Path(),
) -> None:
    pyproject_filepath = Path(parent_dir, "pyproject.toml")
    if not pyproject_filepath.exists():
        raise ValueError("The file 'pyproject.toml' doesn't exists.")
    pyproject_toml = toml.load(pyproject_filepath)
    if "tool" not in pyproject_toml:
        pyproject_toml["tool"] = {}
    if "mypy" in pyproject_toml["tool"]:
        raise ValueError("tool.mypy is already configured.")
    else:
        pyproject_toml["tool"]["mypy"] = {}
    if "overrides" in pyproject_toml["tool"]:
        raise ValueError("tool.mypy is already configured.")
    else:
        pyproject_toml["tool"]["mypy"]["overrides"] = [
            {
                "module": ["importlib_metadata.*"],
                "ignore_missing_imports": True,
            }
        ]
    with open(pyproject_filepath, "w") as f:
        toml.dump(pyproject_toml, f)
