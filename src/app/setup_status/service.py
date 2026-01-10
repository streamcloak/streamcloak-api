import json
from pathlib import Path
from typing import Dict

from fastapi import HTTPException

# Path to the persistent storage file
# Ensure the directory is writable by the user running FastAPI
JSON_FILE_PATH = Path("/opt/streamcloak/config/setup_state.json")


class SetupStateService:
    def __init__(self):
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """
        Creates the JSON file with an empty object if it does not exist.
        """
        if not JSON_FILE_PATH.exists():
            try:
                # Create directory if it doesn't exist
                JSON_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
                # Initialize empty JSON object
                with open(JSON_FILE_PATH, "w") as f:
                    json.dump({}, f)
            except IOError as e:
                # Log this error in production
                print(f"Error initializing setup state file: {e}")

    def get_all_states(self) -> Dict[str, int]:
        """
        Reads the JSON file and returns the dictionary.
        """
        try:
            if not JSON_FILE_PATH.exists():
                return {}

            with open(JSON_FILE_PATH, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            # If file is corrupted, return empty or handle accordingly
            return {}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read setup states: {str(e)}") from e

    def update_state(self, setting_key: str, state: int) -> Dict[str, int]:
        """
        Updates a specific key with a new state and saves to disk.
        Atomic write approach is recommended for high concurrency,
        but direct write is sufficient for single-user config.
        """
        current_data = self.get_all_states()

        # Update the value
        current_data[setting_key] = state

        try:
            with open(JSON_FILE_PATH, "w") as f:
                json.dump(current_data, f, indent=4)
            return current_data
        except IOError as e:
            raise HTTPException(status_code=500, detail=f"Failed to save setup state: {str(e)}") from e

    def get_state(self, setting_key: str) -> int:
        """
        Returns the state for a specific key. Default to 0 (Pending) if not found.
        """
        data = self.get_all_states()
        return data.get(setting_key, 0)
