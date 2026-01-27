import pytest
import os
import shutil
from unittest.mock import MagicMock
from src.core.config_manager import ConfigManager

@pytest.fixture
def temp_game_dir(tmp_path):
    """Creates a temporary game directory for testing."""
    game_dir = tmp_path / "StarCitizen" / "LIVE" / "user" / "client" / "0" / "CustomCharacters"
    game_dir.mkdir(parents=True, exist_ok=True)
    return str(game_dir)

@pytest.fixture
def mock_config_manager(temp_game_dir):
    """Mocks ConfigManager to return the temporary game directory."""
    mock = MagicMock(spec=ConfigManager)
    mock.get_game_path.return_value = temp_game_dir
    return mock
