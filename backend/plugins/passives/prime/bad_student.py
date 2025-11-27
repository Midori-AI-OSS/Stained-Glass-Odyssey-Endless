from dataclasses import dataclass
from typing import ClassVar

from plugins.passives.normal.bad_student import BadStudentBase


@dataclass
class BadStudentPrime(BadStudentBase):
    """Prime-tier Bad Student passive with brutal scheduling power."""

    plugin_type = "passive"
    id = "bad_student_prime"
    name = "Bad Student (Prime)"
    stack_strength: ClassVar[float] = 1.5


__all__ = ["BadStudentPrime"]
