import re

def is_bot(name: str) -> bool:
    return "bot" in name.lower()

def is_temp(name: str) -> bool:
    pattern = re.compile(r"^~\d{4}(?:-\d{1,5})+$")
    return bool(pattern.fullmatch(name))