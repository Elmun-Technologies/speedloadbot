def build_progress_bar(percentage: float, length: int = 10) -> str:
    filled_blocks = int((percentage / 100) * length)
    empty_blocks = length - filled_blocks
    bar = "█" * filled_blocks + "░" * empty_blocks
    return f"{bar} {int(percentage)}%"
