from rpc import RPCServer
import threading
import time
import json
import os
from typing import Any, Dict, Optional
import logging

class RedisClone:
    def __init__(self, snapshot_interval: int = 30, snapshot_file: str = "redis_snapshot.json"):
        self.data_store: Dict[str, Any] = {}
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.snapshot_interval = snapshot_interval
        self.snapshot_file = snapshot_file
        self.last_snapshot_time = time.time()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='redis_clone.log'
        )
        
        # Load existing data if available
        self._load_snapshot()
        
        # Start background snapshot thread
        self.snapshot_thread = threading.Thread(target=self._periodic_snapshot, daemon=True)
        self.snapshot_thread.start()

    def _load_snapshot(self) -> None:
        """Load data from snapshot file if it exists."""
        try:
            if os.path.exists(self.snapshot_file):
                with open(self.snapshot_file, 'r') as f:
                    self.data_store = json.load(f)
                logging.info(f"Loaded snapshot from {self.snapshot_file}")
        except Exception as e:
            logging.error(f"Error loading snapshot: {str(e)}")

    def _save_snapshot(self) -> None:
        """Save current data store to snapshot file."""
        try:
            with self.lock:
                with open(self.snapshot_file, 'w') as f:
                    json.dump(self.data_store, f)
            self.last_snapshot_time = time.time()
            logging.info("Snapshot saved successfully")
        except Exception as e:
            logging.error(f"Error saving snapshot: {str(e)}")

    def _periodic_snapshot(self) -> None:
        """Periodically save snapshots in the background."""
        while True:
            time.sleep(self.snapshot_interval)
            if time.time() - self.last_snapshot_time >= self.snapshot_interval:
                self._save_snapshot()

    def set(self, key: str, value: Any) -> str:
        """Set key-value pair with error handling and logging."""
        try:
            with self.lock:
                self.data_store[key] = value
                logging.info(f"Set key: {key}")
                return "OK"
        except Exception as e:
            logging.error(f"Error setting key {key}: {str(e)}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value for key with error handling."""
        try:
            with self.lock:
                value = self.data_store.get(key)
                if value is None:
                    logging.info(f"Key not found: {key}")
                return value
        except Exception as e:
            logging.error(f"Error getting key {key}: {str(e)}")
            raise

    def delete(self, key: str) -> Optional[Any]:
        """Delete key with error handling."""
        try:
            with self.lock:
                value = self.data_store.pop(key, None)
                if value is not None:
                    logging.info(f"Deleted key: {key}")
                return value
        except Exception as e:
            logging.error(f"Error deleting key {key}: {str(e)}")
            raise

    def keys(self) -> list:
        """Get all keys with error handling."""
        try:
            with self.lock:
                return list(self.data_store.keys())
        except Exception as e:
            logging.error(f"Error getting keys: {str(e)}")
            raise

    def flushall(self) -> str:
        """Clear all data with error handling."""
        try:
            with self.lock:
                self.data_store.clear()
                self._save_snapshot()  # Save empty state
                logging.info("Executed FLUSHALL command")
                return "OK"
        except Exception as e:
            logging.error(f"Error in FLUSHALL: {str(e)}")
            raise

    def append(self, key: str, value: str) -> Any:
        """Append to string value with type checking and error handling."""
        try:
            with self.lock:
                if key in self.data_store:
                    if isinstance(self.data_store[key], str):
                        self.data_store[key] += value
                        logging.info(f"Appended to key: {key}")
                        return len(self.data_store[key])
                    else:
                        msg = f"Value for key {key} is not a string"
                        logging.warning(msg)
                        return msg
                else:
                    msg = f"Key {key} does not exist"
                    logging.warning(msg)
                    return msg
        except Exception as e:
            logging.error(f"Error appending to key {key}: {str(e)}")
            raise