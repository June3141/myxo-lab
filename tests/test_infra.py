"""Pulumi project structure tests."""

from pathlib import Path

import yaml

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


def test_infra_directory_exists():
    assert INFRA_DIR.is_dir(), "infra/ directory must exist"


def test_pulumi_yaml_exists_and_valid():
    pulumi_yaml = INFRA_DIR / "Pulumi.yaml"
    assert pulumi_yaml.is_file(), "infra/Pulumi.yaml must exist"

    data = yaml.safe_load(pulumi_yaml.read_text())
    assert data["name"] == "myxo-lab"
    assert data["runtime"] == "python"
    assert "description" in data


def test_pulumi_dev_yaml_exists_and_valid():
    pulumi_dev_yaml = INFRA_DIR / "Pulumi.dev.yaml"
    assert pulumi_dev_yaml.is_file(), "infra/Pulumi.dev.yaml must exist"

    data = yaml.safe_load(pulumi_dev_yaml.read_text())
    assert data is not None, "Pulumi.dev.yaml must not be empty"


def test_main_py_exists():
    main_py = INFRA_DIR / "__main__.py"
    assert main_py.is_file(), "infra/__main__.py must exist"

    content = main_py.read_text()
    assert "import pulumi\n" in content
    assert "import pulumi_github" in content
    assert "pulumi.export(" in content
