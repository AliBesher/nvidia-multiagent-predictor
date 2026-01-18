"""Test timezone handling"""
from datetime import datetime
from zoneinfo import ZoneInfo

israel_time = datetime.now()
us_et_time = datetime.now(ZoneInfo("America/New_York"))

print("="*60)
print("TIMEZONE TEST")
print("="*60)
print(f"Your computer (Israel): {israel_time}")
print(f"US Eastern Time:        {us_et_time}")
print(f"\nTarget date will be:    {us_et_time.strftime('%Y-%m-%d')}")
print("="*60)
