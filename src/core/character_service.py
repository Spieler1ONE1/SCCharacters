import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

from src.core.config_manager import ConfigManager
from src.core.models import Character

logger = logging.getLogger(__name__)

class CharacterService:
    """
    Service class to handle business logic for Character operations:
    - Installation (logic/verification)
    - Uninstallation
    - Deployment to other environments (PTU, etc)
    - Backup
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._observer = None
        self._watcher_running = False

    def start_watcher(self, on_change_callback):
        """
        Starts watching the CustomCharacters folder for changes.
        """
        if self._watcher_running:
            return

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            path = self.get_game_path()
            if not path.exists():
                return

            class Handler(FileSystemEventHandler):
                def on_any_event(self, event):
                    if event.is_directory:
                        return
                    if event.src_path.endswith('.chf') or event.src_path.endswith('.json'):
                         # Use a small debounce or just callback
                         on_change_callback()

            self._event_handler = Handler()
            self._observer = Observer()
            self._observer.schedule(self._event_handler, str(path), recursive=False)
            self._observer.start()
            self._watcher_running = True
            logger.info(f"Started file watcher on {path}")
        except ImportError:
            logger.warning("Watchdog not installed. File watching disabled.")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")

    def stop_watcher(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._watcher_running = False

    def get_game_path(self) -> Path:
        """Returns the configured game path as a Path object."""
        return Path(self.config_manager.get_game_path())

    def uninstall_character(self, character: Character) -> bool:
        """
        Uninstalls a character by removing its .chf and .json files.
        Returns True if successful (or file didn't exist), False on error.
        """
        try:
            path = self.get_game_path()
            
            # Determine filename
            filename = character.local_filename
            if not filename:
                # Fallback logic to guess filename
                safe_name = "".join([c for c in character.name if c.isalnum() or c in (' ', '.', '-', '_')]).strip()
                filename = f"{safe_name}.chf"
                if not (path / filename).exists():
                     filename = f"{safe_name.replace(' ', '_')}.chf"

            file_path = path / filename
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted character file: {file_path}")
                
                # Also remove json if exists (same basename)
                json_path = file_path.with_suffix(".json")
                if json_path.exists():
                    try:
                        json_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete metadata {json_path}: {e}")
                
                return True
            else:
                logger.warning(f"File to uninstall not found: {file_path}")
                return False 
                
        except Exception as e:
            logger.error(f"Error uninstalling character {character.name}: {e}")
            raise e

    def deploy_to_ptu(self) -> Tuple[int, int, List[str]]:
        """
        Copies characters from current (LIVE) to PTU/EPTU/TECH-PREVIEW if they exist.
        Returns a tuple: (files_copied, environments_found, list_of_env_names).
        Raises Exception on failure.
        """
        live_path = self.get_game_path()
        if not live_path.exists():
            raise FileNotFoundError("Source path not found")

        # Logic: We are at .../LIVE/USER/Client/0/CustomCharacters
        # We want to find .../PTU/... etc.
        # This assumes the standard structure: <Root>/StarCitizen/<Env>/USER/Client/0/CustomCharacters
        
        # Robust navigation: Search up for "StarCitizen" directory
        sc_root = None
        current = live_path
        # Traverse up to 6 levels to be safe
        for _ in range(6):
            if current.name == "StarCitizen":
                sc_root = current
                break
            current = current.parent
            if current == current.parent: # Reached root drive
                break
        
        if not sc_root:
             # Fallback: assume strict relative path if standard folder structure
             # LIVE / USER / Client / 0 / CustomCharacters -> 5 parents up to StarCitizen
             if "StarCitizen" in live_path.parts:
                 # This handles cases where user might have nested it differently but kept "StarCitizen" name
                 # We already tried walking up, maybe the folder name isn't "StarCitizen"?
                 # Let's try to assume the common 'Roberts Space Industries/StarCitizen' structure or just siblings of "LIVE"
                 # Parents: .parent (0), .parent (Client), .parent (USER), .parent (LIVE)
                 # Wait, LIVE is usually the env folder.
                 # path = .../StarCitizen/LIVE/USER/Client/0/CustomCharacters
                 # So LIVE is path.parents[4]
                 pass
             
             # If we couldn't find "StarCitizen" folder specifically, let's try to find the "Env" folder parent
             # usually "LIVE".
             # If user set path to X:/CustomCharacters we are lost unless we guess.
             # Let's try to go up 5 levels and assume that's the base for parallel envs.
             sc_root = live_path.parents[5]

        deploy_targets = ["PTU", "EPTU", "TECH-PREVIEW"]
        found_targets = []
        
        # 1. Check Custom PTU Path first
        custom_ptu = self.config_manager.get_custom_ptu_path()
        if custom_ptu and Path(custom_ptu).exists():
             found_targets.append(("Custom PTU", Path(custom_ptu)))
        
        # Verify which targets exist
        for target in deploy_targets:
            # We look for folders named PTU, EPTU parallel to the folder that contains "USER"
            # Wait, strict structure is: StarCitizen / [LIVE|PTU] / USER / ...
            # So we look for siblings of the directory that CONTAINS "USER".
            # Usually live_path is .../LIVE/USER/Client/0/CustomCharacters
            # live_path.parents[3] is .../LIVE/USER
            # live_path.parents[4] is .../LIVE  <-- The Environment Folder
            # So we want siblings of live_path.parents[4]
            
            # Let's be safer: Identify the environment directory.
            # It's likely the one 5 levels up.
            try:
                env_dir_parent = live_path.parents[5] # .../StarCitizen
                candidate_env = env_dir_parent / target
                
                if candidate_env.exists():
                    # Construct full path
                    target_full = candidate_env / "USER" / "Client" / "0" / "CustomCharacters"
                    
                    # Ensure it exists (create if needed, if parent env exists)
                    try:
                        target_full.mkdir(parents=True, exist_ok=True)
                        found_targets.append((target, target_full))
                    except Exception as e:
                        logger.warning(f"Could not create dir for {target}: {e}")
            except IndexError:
                # Path too short?
                continue

        if not found_targets:
            return 0, 0, []

        count = 0
        # Get all .chf files
        files = list(live_path.glob('*.chf'))
        
        for f in files:
            for _, dest_path in found_targets:
                shutil.copy2(f, dest_path / f.name)
            count += 1
            
        return count, len(found_targets), [t[0] for t in found_targets]

    def create_backup(self, target_zip_path: str) -> None:
        """
        Creates a zip backup of all installed characters.
        """
        source_dir = self.get_game_path()
        if not source_dir.exists():
             raise FileNotFoundError("Source directory not found")

        with zipfile.ZipFile(target_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Parse directory
            for file_path in source_dir.iterdir():
                if file_path.is_file() and (file_path.suffix == '.chf' or file_path.suffix == '.json'):
                    zipf.write(file_path, arcname=file_path.name)

    def save_custom_thumbnail(self, character: Character, image_path: str) -> bool:
        """
        Saves a custom thumbnail for the character.
        The image is renamed to match the character filename + _thumb.jpg
        """
        path = self.get_game_path()
        filename = character.local_filename
        if not filename:
             # Try to resolve filename if not set (fallback)
             safe_name = "".join([c for c in character.name if c.isalnum() or c in (' ', '.', '-', '_')]).strip()
             filename = f"{safe_name}.chf"
             
        base_name = Path(filename).stem
        target_path = path / f"{base_name}_thumb.jpg"
        
        try:
            # Resize/Format check? For now just copy or convert to jpg.
            from PIL import Image
            img = Image.open(image_path)
            # Resize to reasonable thumb size if huge
            img.thumbnail((400, 400)) # Max 400px
            img = img.convert('RGB')
            img.save(target_path, "JPEG", quality=90)
            logger.info(f"Saved custom thumbnail: {target_path}")
            return True
        except ImportError:
            # Fallback if PIL not available (though standard usually)
            # Install PIL if missing
            shutil.copy2(image_path, target_path)
            return True
        except Exception as e:
            logger.error(f"Failed to save thumbnail: {e}")
            return False

    def restore_backup(self, zip_path: str) -> int:
        """
        Restores characters from a zip backup to the game path.
        Returns the number of characters (.chf files) restored.
        """
        path = self.get_game_path()
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise Exception(f"Destination directory does not exist and cannot be created: {e}")

        count = 0
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Filter for .chf and .json files to be safe
                files_to_extract = [f for f in zipf.namelist() if f.endswith('.chf') or f.endswith('.json')]
                
                for file in files_to_extract:
                    # Security check: prevent directory traversal
                    if ".." in file or file.startswith("/") or file.startswith("\\"):
                        logger.warning(f"Skipping suspicious file in backup: {file}")
                        continue
                        
                    zipf.extract(file, path)
                    if file.endswith('.chf'):
                        count += 1
                        
            logger.info(f"Restored {count} characters from backup: {zip_path}")
            return count
            
        except zipfile.BadZipFile:
            raise Exception("Invalid zip file.")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise e


    def update_character_metadata(self, character: Character, new_name: str, new_desc: str, new_tags: List[str], new_author: str = None) -> bool:
        """
        Updates the local .json metadata file for an installed character.
        Does NOT rename the .chf file to avoid breaking game links, but updates the display name in JSON.
        """
        path = self.get_game_path()
        filename = character.local_filename
        
        if not filename:
            return False
            
        json_path = (path / filename).with_suffix('.json')
        
        if not json_path.exists():
            return False
            
        try:
            # Read existing
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Update fields
            data['name'] = new_name
            data['description'] = new_desc
            data['tags'] = new_tags
            if new_author is not None:
                data['author'] = new_author
            # We don't change 'id' or internal filename
            
            # Save
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Updated metadata for {character.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False


            
    def repair_library(self) -> dict:
        """
        Scans the library for inconsistencies:
        1. Deletes orphaned .json files (no matching .chf)
        2. Creates default .json for orphaned .chf files
        
        Returns a summary dict.
        """
        path = self.get_game_path()
        if not path.exists():
            return {"orphans_removed": 0, "metadata_created": 0}
            
        orphans_removed = 0
        metadata_created = 0
        
        # Get all files
        all_files = list(path.iterdir())
        chf_files = {f.stem for f in all_files if f.suffix.lower() == '.chf'}
        json_files = {f.stem for f in all_files if f.suffix.lower() == '.json'}
        
        # 1. Check for orphaned JSONs
        for stem in json_files:
            if stem not in chf_files:
                try:
                    (path / f"{stem}.json").unlink()
                    orphans_removed += 1
                except Exception as e:
                    logger.error(f"Failed to remove orphan json {stem}: {e}")
                    
        # 2. Check for missing JSONs
        from src.core.models import Character
        from datetime import datetime
        
        for stem in chf_files:
            if stem not in json_files:
                # Create default metadata
                try:
                    file_stat = (path / f"{stem}.chf").stat()
                    # Use filename as name, replace underscores
                    name = stem.replace('_', ' ').title()
                    
                    data = {
                        "id": stem, # Use stem as ID
                        "name": name,
                        "description": "Recovered by Maintenance Tool",
                        "author": "Unknown",
                        "download_url": "",
                        "image_url": "",
                        "installed_at": file_stat.st_mtime,
                        "tags": ["Recovered"]
                    }
                    
                    with open(path / f"{stem}.json", 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4)
                        
                    metadata_created += 1
                except Exception as e:
                     logger.error(f"Failed to create metadata for {stem}: {e}")

        logger.info(f"Library repair: Removed {orphans_removed} orphans, Created {metadata_created} metadata files.")
        
        return {
            "orphans_removed": orphans_removed, 
            "metadata_created": metadata_created
        }
        return {
            "orphans_removed": orphans_removed, 
            "metadata_created": metadata_created
        }

    def validate_library_integrity(self) -> List[dict]:
        """
        Scans all .chf files and checks if they have a valid header/size.
        Returns a list of dicts with error details: {'filename': str, 'error': str}
        """
        path = self.get_game_path()
        errors = []
        
        if not path.exists():
            return []
            
        for file_path in path.glob("*.chf"):
            try:
                if file_path.stat().st_size == 0:
                    errors.append({'filename': file_path.name, 'error': 'Empty file (0 bytes)'})
                    continue
                    
                # Read first bytes
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    # SC characters usually are binary or encoded. 
                    # We just check we can read it. 
                    # TODO: Identify known magic bytes for CryXml or similar if public.
                    pass
            except Exception as e:
                errors.append({'filename': file_path.name, 'error': str(e)})
                
        return errors

    def _get_storage_path(self) -> Path:
        """Returns path to the '_storage' folder inside CustomCharacters used for swapping loadouts."""
        path = self.get_game_path() / "_storage"
        path.mkdir(exist_ok=True)
        return path

    def deploy_collection_as_loadout(self, collection_name: str, collection_manager) -> Tuple[int, int]:
        """
        Implementation of the Loadout System.
        1. Moves ALL characters from root CustomCharacters to _storage.
        2. Moves characters belonging to 'collection_name' from _storage (or root) back to root.
        
        Returns (active_count, stored_count)
        """
        game_path = self.get_game_path()
        storage_path = self._get_storage_path()
        
        if not game_path.exists():
            return 0, 0
            
        target_names = set(collection_manager.collections.get(collection_name, []))
        
        # 1. Consolidate everything to storage first
        # (This effectively "Unequips" everything)
        # We move .chf and .json
        moved_to_storage = 0
        
        # Move From Game -> Storage
        for file_path in game_path.iterdir():
            if file_path.is_file() and file_path.suffix in ['.chf', '.json']:
                # Move to storage
                try:
                    shutil.move(str(file_path), str(storage_path / file_path.name))
                    moved_to_storage += 1
                except Exception as e:
                    logger.error(f"Failed to move {file_path.name} to storage: {e}")

        # 2. Deploy requested collection
        # Move From Storage -> Game
        deployed_count = 0
        
        # Iterate storage to find matches
        # Note: target_names usually contains 'Project Name' or 'Filename' depending on how it was saved.
        # Collection Manager stores 'character.name' usually
        # But we need to match filename.
        # We need to map Name -> Filename.
        # This is tricky if metadata is separate. 
        # Strategy: Scan storage, read JSONs (names) to match, then move.
        
        # Pre-scan storage for ID/Name mapping
        storage_map = {} # Name -> [chf_path, json_path]
        
        for json_file in storage_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name')
                    if name:
                        stem = json_file.stem
                        chf_path = storage_path / f"{stem}.chf"
                        if chf_path.exists():
                            storage_map[name] = (chf_path, json_file)
            except: 
                continue
                
        # Also map by filename just in case collection stores IDs
        
        for target in target_names:
            # Check if target is in storage map
            paths = storage_map.get(target)
            
            if paths:
                chf, meta = paths
                try:
                    shutil.move(str(chf), str(game_path / chf.name))
                    shutil.move(str(meta), str(game_path / meta.name))
                    deployed_count += 1
                except Exception as e:
                    logger.error(f"Failed to deploy {target}: {e}")
            else:
                # Maybe target is the filename?
                # Check if target exists as file in storage
                potential_chf = storage_path / f"{target}.chf"
                if potential_chf.exists():
                     potential_json = storage_path / f"{target}.json"
                     try:
                        shutil.move(str(potential_chf), str(game_path / potential_chf.name))
                        if potential_json.exists():
                             shutil.move(str(potential_json), str(game_path / potential_json.name))
                        deployed_count += 1
                     except Exception as e:
                        print(e)

        return deployed_count, moved_to_storage
