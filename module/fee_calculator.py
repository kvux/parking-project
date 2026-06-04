from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)

PARKING_RATE_PER_HOUR = 10000
MINIMUM_CHARGE_HOURS = 1
GRACE_PERIOD_MINUTES = 5  # Free parking for first 5 minutes

def calculate_fee(entry_time, exit_time=None, discount_percent=0):
    """
    Calculate parking fee based on duration
    
    Args:
        entry_time: datetime object (required)
        exit_time: datetime object (defaults to now)
        discount_percent: float between 0-100 (optional)
    
    Returns:
        dict with fee details
    
    Raises:
        ValueError: if times are invalid
        TypeError: if inputs are wrong type
    """
    # Input validation
    if not isinstance(entry_time, datetime):
        raise TypeError("entry_time must be a datetime object")
    
    if exit_time is None:
        exit_time = datetime.now()
    elif not isinstance(exit_time, datetime):
        raise TypeError("exit_time must be a datetime object")
    
    if not isinstance(discount_percent, (int, float)) or discount_percent < 0 or discount_percent > 100:
        raise ValueError("discount_percent must be between 0-100")
    
    # Check time logic
    if entry_time > exit_time:
        raise ValueError("entry_time cannot be after exit_time")
    
    # Calculate duration
    duration = exit_time - entry_time
    total_seconds = duration.total_seconds()
    hours_actual = total_seconds / 3600
    
    # Apply grace period (free parking for first 15 mins)
    if hours_actual <= (GRACE_PERIOD_MINUTES / 60):
        billable_hours = 0
        fee = 0
        discount_amount = 0
        logger.info(f"Grace period applied - parking duration: {hours_actual:.2f} hours")
    else:
        # Round up to nearest hour (minimum 1 hour charge)
        billable_hours = max(MINIMUM_CHARGE_HOURS, math.ceil(hours_actual))
        
        # Calculate base fee
        base_fee = billable_hours * PARKING_RATE_PER_HOUR
        
        # Apply discount
        discount_amount = base_fee * (discount_percent / 100)
        fee = base_fee - discount_amount
    
    return {
        "entry_time": entry_time.isoformat(),
        "exit_time": exit_time.isoformat(),
        "duration_hours": round(hours_actual, 2),
        "billable_hours": billable_hours,
        "base_fee": round(billable_hours * PARKING_RATE_PER_HOUR if billable_hours > 0 else 0, 2),
        "discount_percent": discount_percent,
        "discount_amount": round(discount_amount if billable_hours > 0 else 0, 2),
        "fee": round(fee, 2),
        "rate_per_hour": PARKING_RATE_PER_HOUR
    }

def format_fee_report(records):
    """
    Generate fee report from multiple records
    
    Args:
        records: list of fee dictionaries
    
    Returns:
        dict with aggregated statistics
    
    Raises:
        TypeError: if records is not a list
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    
    if not records:
        return {
            "total_records": 0,
            "total_revenue": 0,
            "average_fee": 0,
            "min_fee": 0,
            "max_fee": 0
        }
    
    fees = [r.get('fee', 0) for r in records if isinstance(r, dict)]
    
    if not fees:
        logger.warning("No valid fees found in records")
        return {
            "total_records": len(records),
            "total_revenue": 0,
            "average_fee": 0,
            "min_fee": 0,
            "max_fee": 0
        }
    
    total_fee = sum(fees)
    
    return {
        "total_records": len(records),
        "total_revenue": round(total_fee, 2),
        "average_fee": round(total_fee / len(fees), 2),
        "min_fee": round(min(fees), 2),
        "max_fee": round(max(fees), 2)
    }
