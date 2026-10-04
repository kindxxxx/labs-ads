"""Каталог лабораторных — seed-источник для БД.

Ссылки на ejudge не хранятся: contest_id = база предмета + номер лабы.
  PP1 → 101, 102, 103 …
  ADS → 201, 202, 203 …
  PP2 → 301, 302, 303 … (базу можно поправить в CONTEST_ID_BASE)
"""

from __future__ import annotations

from dataclasses import dataclass

EJUDGE_CLIENT_URL = "http://ejudge.kz/new-client"

# База contest_id для первой лабы предмета; lab N → base + N.
CONTEST_ID_BASE: dict[str, int] = {
    "PP1": 100,
    "ADS": 200,
    "PP2": 300,
}


@dataclass(frozen=True)
class LabSeed:
    lab_number: int
    languages: tuple[str, ...]
    price: int
    description: str = ""
    requirements: str = ""


LABS: dict[str, dict[int, LabSeed]] = {
    "PP1": {
        1: LabSeed(1, ("Python", "C++"), 1500, "Лабораторная 1"),
        2: LabSeed(2, ("Python", "C++"), 1500, "Лабораторная 2"),
        3: LabSeed(3, ("Python",), 1500, "Лабораторная 3"),
    },
    "PP2": {
        1: LabSeed(1, ("C++",), 1500, "Лабораторная 1"),
        2: LabSeed(2, ("C++",), 1500, "Лабораторная 2"),
    },
    "ADS": {
        1: LabSeed(1, ("C++",), 2000, "Лабораторная 1"),
        2: LabSeed(2, ("C++",), 2000, "Лабораторная 2"),
    },
}

SUBJECTS: tuple[str, ...] = ("ADS", "PP1", "PP2")


@dataclass(frozen=True)
class SubjectPlatform:
    title: str
    platform: str


SUBJECT_PLATFORMS: dict[str, SubjectPlatform] = {
    "ADS": SubjectPlatform("Algorithms & Data Structures", "ejudge"),
    "PP1": SubjectPlatform("Programming Principles 1", "ejudge"),
    "PP2": SubjectPlatform("Programming Principles 2", "ejudge"),
}


def contest_id(subject: str, lab_number: int) -> int:
    base = CONTEST_ID_BASE.get(subject)
    if base is None:
        raise ValueError(f"Неизвестный предмет: {subject}")
    return base + lab_number


def lab_contest_url(subject: str, lab_number: int) -> str:
    return f"{EJUDGE_CLIENT_URL}?contest_id={contest_id(subject, lab_number)}"
