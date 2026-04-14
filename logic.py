from datetime import date, timedelta
import calendar

# algorith to find least tokens for search by quantization
def minimize_dates(dates: list[date]) -> list[str]:
    if not dates:
        return []
    
    date_set = set(dates)
    results = []
    processed = set()
    
    sorted_dates = sorted(dates)
    
    for d in sorted_dates:
        if d in processed:
            continue
            
        year, month = d.year, d.month
        last_day = calendar.monthrange(year, month)[1]
        
        # full yr (YYYY*)
        year_dates = {date(year, m, d) for m in range(1, 13) 
                      for d in range(1, calendar.monthrange(year, m)[1] + 1)}
        if year_dates.issubset(date_set):
            results.append(f"{year}*")
            processed.update(year_dates)
            continue

        # full mo (YYYY-MM*)
        month_dates = {date(year, month, day) for day in range(1, last_day + 1)}
        if month_dates.issubset(date_set):
            results.append(f"{year}-{month:02}*")
            processed.update(month_dates)
            continue
            
        # decade (YYYY-MM-X*)
        decade = d.day // 10
        if decade < 3:
            start_day = max(1, decade * 10)
            end_day = (decade + 1) * 10
        
        # single day
        results.append(d.isoformat())
        processed.add(d)
        
    # deduplicate
    return sorted(list(set(results)))
