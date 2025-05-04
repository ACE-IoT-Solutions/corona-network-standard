"""
Tests for the Corona Network Standard CLI tool, focusing on validation.
"""
import pytest
from click.testing import CliRunner
from pathlib import Path

from src.corona_network_standard.main import cli

@pytest.fixture
def runner():
    """Provides a Click test runner instance for invoking CLI commands."""
    return CliRunner()

def test_generate_and_validate(runner: CliRunner, tmp_path: Path):
    """
    Tests the full generate and validate workflow.

    1. Runs the `generate` command to create an example RDF file.
    2. Asserts that the generation was successful and the file was created.
    3. Runs the `validate` command on the generated file.
    4. Asserts that the validation command exits successfully and reports conformance.

    Args:
        runner: The Click test runner fixture.
        tmp_path: The pytest fixture providing a temporary directory path.
    """
    output_file = tmp_path / "test-network-data.ttl"

    # 1. Run the generate command
    generate_result = runner.invoke(cli, ["generate", "-o", str(output_file)])

    # Assert generation was successful
    assert generate_result.exit_code == 0, f"Generate command failed: {generate_result.output}"
    assert "Generation Complete" in generate_result.output
    assert output_file.exists(), "Generated output file does not exist."
    assert output_file.stat().st_size > 0, "Generated output file is empty."

    # 2. Run the validate command on the generated file
    validate_result = runner.invoke(cli, ["validate", str(output_file)])

    # Assert validation was successful and conforms
    assert validate_result.exit_code == 0, f"Validate command failed: {validate_result.output}"
    assert "Data graph conforms to the SHACL shapes." in validate_result.output

