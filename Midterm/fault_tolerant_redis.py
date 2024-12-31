from rpc import RPCServer
import threading
import time
import json
import os
from typing import Any, Dict, List, Optional
import logging
from collections import defaultdict

class FaultTolerantRedisClone:
    def __init__(self, snapshot_interval: int = 30, snapshot_file: str = "redis_snapshot.json"):
        self.data_store: Dict[str, Any] = {}
        self.sorted_sets: Dict[str, List[tuple]] = {} 
        self.expiry_times: Dict[str, float] = {} 
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.lock_list = threading.Lock()
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
        
        # Xử lí key hết hạn 
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_keys, daemon=True)
        self.cleanup_thread.start()

        # Start background snapshot thread
        self.snapshot_thread = threading.Thread(target=self._periodic_snapshot, daemon=True)
        self.snapshot_thread.start()

    def _cleanup_expired_keys(self):
        """Remove keys that have expired."""
        while True:
            time.sleep(1)  # Check every second
            with self.lock:
                current_time = time.time()
                expired_keys = [
                    key for key, expire_time in self.expiry_times.items()
                    if expire_time <= current_time
                ]
                for key in expired_keys:
                    self.data_store.pop(key, None)
                    self.expiry_times.pop(key, None)
                    logging.info(f"Key expired and removed: {key}")

    def _load_snapshot(self) -> None:
        """Load data from snapshot file if it exists."""
        try:
            if os.path.exists(self.snapshot_file):
                with open(self.snapshot_file, 'r') as f:
                    snapshot_data = json.load(f)
                    self.data_store = snapshot_data.get('data', {})
                    self.expiry_times = {
                        k: float(v) for k, v in snapshot_data.get('expiry', {}).items()
                    }
                    self.sorted_sets = snapshot_data.get('sorted_sets', {})
                logging.info(f"Loaded snapshot from {self.snapshot_file}")
        except Exception as e:
            logging.error(f"Error loading snapshot: {str(e)}")

    def _save_snapshot(self) -> None:
        """Save current data store to snapshot file."""
        try:
            with self.lock:
                snapshot_data = {
                    'data': self.data_store,
                    'expiry': self.expiry_times,
                    'sorted_sets': self.sorted_sets 
                }
                with open(self.snapshot_file, 'w') as f:
                    json.dump(snapshot_data, f)
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

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> str:
        """Set key-value pair with optional expiry time."""
        try:
            with self.lock:
                self.data_store[key] = value
                if ex is not None:
                    self.expiry_times[key] = time.time() + int(ex)
                    logging.info(f"Set key {key} with {ex} seconds TTL")
                else:
                    # Remove any existing TTL
                    self.expiry_times.pop(key, None)
                    logging.info(f"Set key {key} without TTL")
                return "OK"
        except Exception as e:
            logging.error(f"Error setting key {key}: {str(e)}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value for key with error handling."""
        try:
            with self.lock:
                if key in self.expiry_times:
                    if time.time() >= self.expiry_times[key]:
                        self.data_store.pop(key, None)
                        self.expiry_times.pop(key)
                        return None
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
                self.expiry_times.pop(key, None)
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
                # Only return non-expired keys
                current_time = time.time()
                return [
                    key for key in self.data_store.keys()
                    if key not in self.expiry_times or self.expiry_times[key] > current_time
                ]
        except Exception as e:
            logging.error(f"Error getting keys: {str(e)}")
            raise

    def flushall(self) -> str:
        """Clear all data with error handling."""
        try:
            with self.lock:
                self.data_store.clear()
                self.expiry_times.clear()
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

    def expire(self, key: str, seconds: int) -> bool:
        """Set TTL (time to live) for a key."""
        try:
            with self.lock:
                if key in self.data_store:
                    self.expiry_times[key] = time.time() + int(seconds)
                    logging.info(f"Set TTL for key {key}: {seconds} seconds")
                    return True
                logging.info(f"Key {key} not found for expire")
                return False
        except Exception as e:
            logging.error(f"Error setting expire for key {key}: {str(e)}")
            raise

    def ttl(self, key: str) -> int:
        """Get remaining TTL (time to live) for a key."""
        try:
            with self.lock:
                if key not in self.data_store:
                    logging.info(f"Key {key} not found for TTL check")
                    return -2  # Key không tồn tại
                
                if key not in self.expiry_times:
                    logging.info(f"Key {key} has no TTL set")
                    return -1  # Key không có TTL
                
                remaining = int(self.expiry_times[key] - time.time())
                if remaining <= 0:
                    # Key đã hết hạn
                    self.data_store.pop(key, None)
                    self.expiry_times.pop(key, None)
                    logging.info(f"Key {key} expired during TTL check")
                    return -2
                    
                return remaining
        except Exception as e:
            logging.error(f"Error checking TTL for key {key}: {str(e)}")
            raise

    def persist(self, key: str) -> bool:
        """Remove TTL from a key."""
        try:
            with self.lock:
                if key not in self.data_store:
                    logging.info(f"Key {key} not found for persist")
                    return False
                    
                if key not in self.expiry_times:
                    logging.info(f"Key {key} already has no TTL")
                    return False
                    
                self.expiry_times.pop(key)
                logging.info(f"Removed TTL for key {key}")
                return True
        except Exception as e:
            logging.error(f"Error persisting key {key}: {str(e)}")
            raise
        
    def exists(self, key: str) -> bool:
        try:
            with self.lock:
                logging.info(f"Checking existence of key: {key}") 
                if key in self.data_store:
                    # Check if the key has expired
                    if key in self.expiry_times and self.expiry_times[key] <= time.time():
                        # If it has expired, delete the key from data_store and Expiration_times
                        self.data_store.pop(key, None)
                        self.expiry_times.pop(key, None)
                        logging.info(f"Key {key} is expired and removed.")
                        return False
                    logging.info(f"Key {key} exists and is valid.")
                    return True
                logging.info(f"Key {key} does not exist.")
                return False
        except Exception as e:
            logging.error(f"Error checking existence of key {key}: {str(e)}")
            raise
