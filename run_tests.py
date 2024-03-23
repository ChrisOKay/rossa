"""configure & run tests for pxi framework, show coverage."""

import logging
import subprocess
from enum import Enum
from pathlib import Path
from typing import List, Optional

import coverage
import pytest


class Cov(coverage.Coverage):
    """coverage api."""

    def __init__(
        self,
        exclude_lines: List[str],
        exclude_files: List[str],
        ignore_errors: bool = True,
        report: bool = True,
    ):
        super().__init__()
        for line in exclude_lines:
            self.exclude(line)
        self.exclude_files = exclude_files
        self.ignore_errors = ignore_errors
        self.report = report

    def create_report(self, report_dir: str = "tests/coverage_html_report") -> None:
        """Create report from saved coverage data."""
        if not self.report:
            return
        logging.info("Creating report")
        self.html_report(
            directory=report_dir,
            ignore_errors=self.ignore_errors,
            omit=self.exclude_files,
        )
        self.open_report_in_browser(report_dir)

    @staticmethod
    def open_report_in_browser(report_dir: str = "tests/coverage_html_report") -> None:
        """Open current report in default browser."""
        logging.info("Opening browser")
        subprocess.run(
            ["start", str(Path(__file__).parent / report_dir / "index.html")],
            shell=True,
            check=True,
        )


class PytestExitCodes(Enum):
    """Meaning of pytest's 'main' exit codes."""

    SUCCESS = 0
    SOME_TESTS_FAILED = 1
    TESTS_INTERRUPTED = 2
    INTERNAL_ERROR = 3
    USAGE_ERROR = 4
    NO_TESTS_COLLECTED = 5


class TestRunner:
    """Perform and evaluate tests & coverage report."""

    def __init__(
        self,
        cov: Cov,
        exclude_folders: Optional[list[str]] = None,
        test_folder: str = "tests",
        ignore_errors: bool = True,
    ):

        self.cov = cov
        self.pytest_param = [test_folder]
        self.pytest_param.append("-rfE")  # show failure and Error summary
        self.pytest_param.append("-W ignore::DeprecationWarning")
        if exclude_folders is not None:
            [self.pytest_param.append(f"--ignore={f}") for f in exclude_folders]
        self.pytest_param.append("--durations=10")
        self.ignore_errors = ignore_errors

    def run(self) -> None:
        """Start coverage, run tests, show report or test failure."""
        logging.info("Starting coverage.py")
        self.cov.start()
        logging.info("Starting pytest")
        exit_code = pytest.main(self.pytest_param)
        self.cov.stop()
        self.cov.save()
        if exit_code:
            logging.error(
                "Pytest reported the following error: %s",
                PytestExitCodes(exit_code).name,
            )
            return
        self.cov.create_report()
        self.delete_coverage_data()

    @staticmethod
    def delete_coverage_data() -> None:
        """Delete .coverage file."""
        (Path(__file__).parent / ".coverage").unlink()


def setup_logger() -> None:
    """Progress logs during test & report generation."""
    logging.basicConfig(encoding="utf-8", level=logging.DEBUG)


def run_tests(create_report: bool = True) -> None:
    """Run tests appropriate for current measurement setup.

    Measure & report coverage if tests ran successful.
    """
    excl_cov_lines = [
        "if __name__ == .__main__.:",
        "if TYPE_CHECKING:",
    ]
    excl_cov_files = [
        "tests/*",
        "*__init__*",
    ]
    cov = Cov(excl_cov_lines, excl_cov_files, report=create_report)
    runner = TestRunner(cov)
    runner.run()


if __name__ == "__main__":
    setup_logger()
    run_tests()
