from datetime import datetime, timezone


def format_date(date: str) -> str:
    try:
        dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
        formatted_posted_at = dt.strftime("%b %d, %Y")
    except (ValueError, AttributeError):
        formatted_posted_at = date

    return formatted_posted_at


def calculate_time_difference(date: str | None) -> str:
    if date is None:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        current_date = datetime.now(timezone.utc)
        time_diff = current_date - dt
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days} days ago"
        elif hours > 0:
            return f"{hours} hours ago"
        elif minutes > 0:
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    except (ValueError, AttributeError):
        return "Unknown"
