from datetime import datetime, timedelta
import re

def get_week_number_in_month(date):
    """Get the week number (1-5) for a given date in its month."""
    first_day = date.replace(day=1)
    dom = date.day
    adjusted_dom = dom + first_day.weekday()
    return (adjusted_dom - 1) // 7 + 1

def get_next_collection_day(day_name, schedule_type=None, schedule_details=None):
    """Calculate the next collection day based on the schedule configuration."""
    if not day_name:
        return None
        
    # Convert day name to lowercase for comparison
    day_name = day_name.lower()
    
    # Map day names to numbers (0 = Monday, 6 = Sunday)
    days = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    if day_name not in days:
        return None
        
    today = datetime.now()
    today_weekday = today.weekday()
    target_weekday = days[day_name]

    if schedule_type == 'weekly':
        # Calculate days until next weekly collection
        days_ahead = target_weekday - today_weekday
        if days_ahead <= 0:  # Target day has passed this week
            days_ahead += 7
        next_date = today + timedelta(days=days_ahead)
        
    elif schedule_type == 'biweekly':
        if not schedule_details:
            return None
            
        # Try to parse the start date from schedule_details
        start_date_match = re.search(r'starting (\d{4}-\d{2}-\d{2})', schedule_details.lower())
        if start_date_match:
            try:
                start_date = datetime.strptime(start_date_match.group(1), '%Y-%m-%d')
                # Calculate days until next biweekly collection
                days_ahead = target_weekday - today_weekday
                if days_ahead <= 0:  # Target day has passed this week
                    days_ahead += 7
                next_date = today + timedelta(days=days_ahead)
                
                # Adjust to next biweekly occurrence if necessary
                days_since_start = (next_date - start_date).days
                if days_since_start % 14 != 0:
                    next_date += timedelta(days=7)
            except ValueError:
                return None
        else:
            # Handle "1st and 3rd Monday" type patterns
            week_patterns = re.findall(r'(\d+)(?:st|nd|rd|th)', schedule_details.lower())
            if week_patterns:
                week_numbers = [int(n) for n in week_patterns]
                # Calculate the next occurrence based on week numbers
                next_date = today
                while True:
                    week_num = get_week_number_in_month(next_date)
                    if next_date.weekday() == target_weekday and week_num in week_numbers and next_date >= today:
                        break
                    next_date += timedelta(days=1)
            else:
                return None
                
    elif schedule_type == 'monthly':
        if not schedule_details:
            return None
            
        # Handle "1st Monday" patterns
        week_match = re.search(r'(\d+)(?:st|nd|rd|th)', schedule_details.lower())
        if week_match:
            week_number = int(week_match.group(1))
            # Calculate the next occurrence
            next_date = today
            while True:
                week_num = get_week_number_in_month(next_date)
                if next_date.weekday() == target_weekday and week_num == week_number and next_date >= today:
                    break
                next_date += timedelta(days=1)
        else:
            # Handle "15th of each month" patterns
            day_match = re.search(r'(\d+)(?:st|nd|rd|th)? of (?:each|every) month', schedule_details.lower())
            if day_match:
                day_of_month = int(day_match.group(1))
                next_date = today
                if today.day > day_of_month:
                    next_date = (today.replace(day=1) + timedelta(days=32)).replace(day=day_of_month)
                else:
                    next_date = today.replace(day=day_of_month)
            else:
                return None
    else:
        # Default to weekly behavior
        days_ahead = target_weekday - today_weekday
        if days_ahead <= 0:  # Target day has passed this week
            days_ahead += 7
        next_date = today + timedelta(days=days_ahead)
        
    return next_date

def format_next_collection(day_name, schedule_type=None, schedule_details=None):
    """Format the next collection day in a user-friendly way."""
    if not day_name:
        return "Not specified"
        
    next_date = get_next_collection_day(day_name, schedule_type, schedule_details)
    if not next_date:
        if schedule_type in ['biweekly', 'monthly'] and not schedule_details:
            return f"Schedule details needed for {schedule_type} pickup"
        return "Invalid schedule"
        
    today = datetime.now()
    days_until = (next_date.date() - today.date()).days
    
    if days_until == 0:
        return "TODAY"
    elif days_until == 1:
        return "TOMORROW"
    elif days_until < 7:
        return f"In {days_until} days"
    else:
        # For longer periods, show the actual date
        return next_date.strftime("%B %d")