from datetime import date time
import math

PARKING_RATE_PER_HOUR = 10000

def calculate_fee(entry_time, exit_time=None);
"""
Calculate parking fee based on duration

Args:
entry_time: datetime object
exit_time: dateime object (defaults to now)

Returns:
dict with fee details
"""
if exit_time is None;
exit_time =datetime.now()

#calculate how long
duration= exit_time - entry_time
total_seconds = duration.total_seconds ()
hours_actual = total_seconds / 3600

#round number
billable_hours = math.ceil(hours_actual

#minimum charge of 1 hour
    if billable_hours < 1:
        billable_hours = 1
fee = billable_hours * PARKING_RATE_PER_HOUR

return {
  "entry_time": entry_time.isoformat(),
        "exit_time": exit_time.isoformat(),
        "duration_hours": round(hours_actual, 2),
        "billable_hours": billable_hours,
        "fee": round(fee, 2),
        "rate_per_hour": PARKING_RATE_PER_HOUR
    }

def format_fee_report(records):
    """Generate fee report from multiple records"""
    total_fee = sum(r.get('fee', 0) for r in records)
    return {
        "total_records": len(records),
        "total_revenue": round(total_fee, 2),
        "average_fee": round(total_fee/len(records), 2) if records else 0
    }

  
