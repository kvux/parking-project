
from datetime import datetime
import csv
import os
import json

LOG_FILE = "logs/entry_exit.csv"
JSON_LOG = "logs/entry_exit.json"

#make sure logs exist
os.makedirs("logs", exist_ok=True)

def log_barrier_event(car_plate, action, spot_id=None):
    """
    Log entry/exit events for barrier system
    
    Args:
        car_plate: string
        action: 'ENTRY' or 'EXIT'
        spot_id: int (optional)
    
    Returns:
        dict with logged event
    """
    timestamp = datetime.now()
    
    event = {
        "timestamp": timestamp.isoformat(),
        "car_plate": car_plate,
        "action": action,
        "spot_id": spot_id,
        "barrier_triggered": True
    }
    
    # log csv
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=event.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(event)
    
    # log json
    json_events = []
    if os.path.exists(JSON_LOG):
        with open(JSON_LOG, 'r') as f:
            try:
                json_events = json.load(f)
            except:
                json_events = []
    
    json_events.append(event)
    
    # only 1000 event
    if len(json_events) > 1000:
        json_events = json_events[-1000:]
    
    with open(JSON_LOG, 'w') as f:
        json.dump(json_events, f, indent=2)
    
    #pront console
    print(f"[BARRIER] {timestamp.strftime('%H:%M:%S')} - {action}: {car_plate}" + 
          (f" at spot {spot_id}" if spot_id else ""))
    
    return event

def get_recent_logs(limit=50):
    """Get recent barrier logs"""
    if not os.path.exists(JSON_LOG):
        return []
    
    with open(JSON_LOG, 'r') as f:
        try:
            logs = json.load(f)
            return logs[-limit:]
        except:
            return []

def get_today_summary():
    """Get summary of today's barrier events"""
    today = datetime.now().date().isoformat()
    entries = 0
    exits = 0
    
    if os.path.exists(JSON_LOG):
        with open(JSON_LOG, 'r') as f:
            try:
                logs = json.load(f)
                for log in logs:
                    if log['timestamp'].startswith(today):
                        if log['action'] == 'ENTRY':
                            entries += 1
                        else:
                            exits += 1
            except:
                pass
    
    return {
        "date": today,
        "total_entries": entries,
        "total_exits": exits,
        "total_vehicles": entries  #asume every entry is unique
    }
