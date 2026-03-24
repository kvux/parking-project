from datetime import datetime
import csv
import os
import json
import fcntl
import logging

LOG_FILE = "logs/entry_exit.csv"
JSON_LOG = "logs/entry_exit.json"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure logs exist
os.makedirs("logs", exist_ok=True)

# Validate action parameter
VALID_ACTIONS = {'ENTRY', 'EXIT'}

def _acquire_lock(f):
    """Acquire file lock (Unix/Linux/Mac)"""
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    except (AttributeError, OSError):
        # Windows fallback - fcntl not available
        pass

def _release_lock(f):
    """Release file lock"""
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (AttributeError, OSError):
        pass

def log_barrier_event(car_plate, action, spot_id=None):
    """
    Log entry/exit events for barrier system with file locking
    
    Args:
        car_plate: string (required)
        action: 'ENTRY' or 'EXIT' (required)
        spot_id: int (optional)
    
    Returns:
        dict with logged event, or None if validation fails
    
    Raises:
        ValueError: if action or car_plate is invalid
    """
    # Validate inputs
    if not isinstance(car_plate, str) or not car_plate.strip():
        raise ValueError("car_plate must be a non-empty string")
    
    action = action.upper()
    if action not in VALID_ACTIONS:
        raise ValueError(f"action must be 'ENTRY' or 'EXIT', got '{action}'")
    
    timestamp = datetime.now()
    
    event = {
        "timestamp": timestamp.isoformat(),
        "car_plate": car_plate.strip().upper(),
        "action": action,
        "spot_id": spot_id,
        "barrier_triggered": True
    }
    
    try:
        # Log to CSV with file lock
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, 'a', newline='') as f:
            _acquire_lock(f)
            try:
                writer = csv.DictWriter(f, fieldnames=event.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(event)
            finally:
                _release_lock(f)
        
        # Log to JSON with file lock
        json_events = []
        if os.path.exists(JSON_LOG):
            with open(JSON_LOG, 'r') as f:
                _acquire_lock(f)
                try:
                    json_events = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("JSON log corrupted, starting fresh")
                    json_events = []
                finally:
                    _release_lock(f)
        
        json_events.append(event)
        
        # Keep last 10,000 events (increased from 1000)
        if len(json_events) > 10000:
            json_events = json_events[-10000:]
        
        with open(JSON_LOG, 'w') as f:
            _acquire_lock(f)
            try:
                json.dump(json_events, f, indent=2)
            finally:
                _release_lock(f)
        
        # Console output
        print(f"[BARRIER] {timestamp.strftime('%H:%M:%S')} - {action}: {event['car_plate']}" + 
              (f" at spot {spot_id}" if spot_id else ""))
        
        return event
    
    except IOError as e:
        logger.error(f"Failed to log event: {e}")
        return None

def get_recent_logs(limit=50):
    """Get recent barrier logs"""
    if not os.path.exists(JSON_LOG):
        return []
    
    try:
        with open(JSON_LOG, 'r') as f:
            _acquire_lock(f)
            try:
                logs = json.load(f)
                return logs[-limit:]
            except json.JSONDecodeError:
                logger.warning("JSON log corrupted")
                return []
            finally:
                _release_lock(f)
    except IOError as e:
        logger.error(f"Failed to read logs: {e}")
        return []

def get_today_summary():
    """Get summary of today's barrier events"""
    today = datetime.now().date().isoformat()
    entries = 0
    exits = 0
    unique_vehicles = set()
    
    if os.path.exists(JSON_LOG):
        try:
            with open(JSON_LOG, 'r') as f:
                _acquire_lock(f)
                try:
                    logs = json.load(f)
                    for log in logs:
                        if log['timestamp'].startswith(today):
                            if log['action'] == 'ENTRY':
                                entries += 1
                            else:
                                exits += 1
                            unique_vehicles.add(log['car_plate'])
                finally:
                    _release_lock(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read summary: {e}")
    
    return {
        "date": today,
        "total_entries": entries,
        "total_exits": exits,
        "unique_vehicles": len(unique_vehicles),
        "vehicle_plates": list(unique_vehicles)
    }