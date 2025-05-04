import pytest
from click.testing import CliRunner
from pathlib import Path

from src.corona_network_standard.main import cli

@pytest.fixture
def runner():
    """Provides a Click test runner."""
    return CliRunner()

def test_generate_and_validate(runner: CliRunner, tmp_path: Path):
    """Tests generating the example network and validating it."""
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

