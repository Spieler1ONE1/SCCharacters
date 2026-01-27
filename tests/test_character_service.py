import os
import pytest
from src.core.character_service import CharacterService
from src.core.models import Character

def test_uninstall_character(mock_config_manager, temp_game_dir):
    # Setup
    service = CharacterService(mock_config_manager)
    
    # Create dummy character files
    char_name = "TestChar"
    chf_path = os.path.join(temp_game_dir, f"{char_name}.chf")
    json_path = os.path.join(temp_game_dir, f"{char_name}.json")
    
    with open(chf_path, 'w') as f:
        f.write("dummy chf content")
    with open(json_path, 'w') as f:
        f.write("{}")
        
    character = Character(
        name=char_name, 
        author="Me", 
        url_detail="", 
        image_url="", 
        download_url="http://test.com/TestChar.chf",
        local_filename=f"{char_name}.chf"
    )
    
    # Action
    result = service.uninstall_character(character)
    
    # Assert
    assert result is True
    assert not os.path.exists(chf_path)
    assert not os.path.exists(json_path)

def test_uninstall_non_existent_character(mock_config_manager, temp_game_dir):
    service = CharacterService(mock_config_manager)
    character = Character(
        name="Ghost", 
        author="Ghost", 
        url_detail="", 
        image_url="", 
        download_url="",
        local_filename="ghost.chf"
    )
    
    # Should return True as the end state (files gone) is achieved, or specific logic?
    # Checking implementation: "Returns True if successful (or file didn't exist)"
    result = service.uninstall_character(character)
    assert result is True
