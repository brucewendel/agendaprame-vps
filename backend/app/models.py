from dataclasses import dataclass

@dataclass
class Room:
    id: int
    name: str
    active: bool
