import pytest
from unittest.mock import MagicMock


@pytest.fixture
def session():
    mock = MagicMock()
    mock.exec.return_value.first.return_value = None
    mock.exec.return_value.all.return_value = []
    return mock


@pytest.fixture
def mock_cursor():
    return MagicMock()


@pytest.fixture
def yaml_file(tmp_path):
    content = """
programming_languages:
  - Python
  - Rust
  - C++
techs:
  - Git
  - Docker
  - Kubernetes
addons:
  - VSCode
  - Sublime Text
  - Postman
"""
    path = tmp_path / "skills.yaml"
    path.write_text(content)
    return str(path)


@pytest.fixture
def empty_yaml_file(tmp_path):
    content = """
programming_languages: []
techs: []
addons: []
"""
    path = tmp_path / "empty_skills.yaml"
    path.write_text(content)
    return str(path)
