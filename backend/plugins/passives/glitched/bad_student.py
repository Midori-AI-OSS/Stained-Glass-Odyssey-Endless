from dataclasses import dataclass
from typing import ClassVar

from plugins.passives.normal.bad_student import BadStudentBase


@dataclass
class BadStudentGlitched(BadStudentBase):
    """Glitched-tier Bad Student passive that nearly freezes opponents in place."""

    plugin_type = "passive"
    id = "bad_student_glitched"
    name = "Bad Student (Glitched)"
    stack_strength: ClassVar[float] = 5.0


__all__ = ["BadStudentGlitched"]
