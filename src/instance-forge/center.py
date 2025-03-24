#!/usr/bin/env python3

from typing import List, Optional

from machine import Machine

class Center:
    """center/stage/level in flexible shop models"""
    def __init__(self, id: int) -> None:
        self.id: int = id
        self.name: str = f"C{id}"
        self.machines: List[Machine] = []
