import sys

def loading_bar(current_value, max_value, length=50):
    progress = (current_value / max_value)
    max_value = max(current_value, max_value)
    progress = min (progress, 1) # Cap progress at 100% if current value exceeds it
    arrow = '|' * int(round(progress * length))
    spaces = ' ' * (length - len(arrow))
    sys.stdout.write(f'\r[{arrow}{spaces}] {int(progress * 100):4}%  - {current_value:5} /{max_value} items')
    sys.stdout.flush()