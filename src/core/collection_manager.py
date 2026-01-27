
import json
import os
import logging
from typing import Dict, List, Set

class CollectionManager:
    """
    Manages custom user collections/groups for characters.
    Data is stored in 'collections.json' in the config directory.
    """
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.file_path = os.path.join(config_dir, "collections.json")
        self.collections: Dict[str, List[str]] = {} # Name -> List of Character Names (IDs)
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.collections = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load collections: {e}")
                self.collections = {}
        else:
            self.collections = {}

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.collections, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save collections: {e}")

    def get_all_collections(self) -> List[str]:
        return list(self.collections.keys())

    def create_collection(self, name: str) -> bool:
        if name not in self.collections:
            self.collections[name] = []
            self.save()
            return True
        return False

    def delete_collection(self, name: str):
        if name in self.collections:
            del self.collections[name]
            self.save()

    def add_to_collection(self, collection_name: str, character_name: str):
        if collection_name in self.collections:
            if character_name not in self.collections[collection_name]:
                self.collections[collection_name].append(character_name)
                self.save()

    def remove_from_collection(self, collection_name: str, character_name: str):
        if collection_name in self.collections:
            if character_name in self.collections[collection_name]:
                self.collections[collection_name].remove(character_name)
                self.save()

    def get_character_collections(self, character_name: str) -> List[str]:
        """Returns a list of collection names this character belongs to."""
        return [col for col, chars in self.collections.items() if character_name in chars]

    def rename_collection(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.collections:
            return False
        if new_name in self.collections:
            return False
            
        # Move data
        self.collections[new_name] = self.collections.pop(old_name)
        self.save()
        return True
