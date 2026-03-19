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
