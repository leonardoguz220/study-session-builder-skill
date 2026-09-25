"""Validación compartida y CLI sin dependencias externas (Python 3.10+)."""

import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
RULES_PATH = SKILL_DIR / "references" / "study_rules.json"


class InputError(ValueError):
    """Error que puede corregir la persona que prepara la entrada."""


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                          object_pairs_hook=unique_keys)
    except FileNotFoundError as exc:
        raise InputError(f"No existe el archivo: {path}") from exc
    except (OSError, UnicodeError) as exc:
        raise InputError(f"No se pudo leer el archivo: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"JSON inválido en línea {exc.lineno}, columna {exc.colno}.") from exc


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"Clave JSON duplicada: {key}")
        result[key] = value
    return result


def parse_date(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InputError(f"{field} debe usar el formato AAAA-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InputError(f"Fecha inválida en {field}: {value}") from exc


def load_rules(path=RULES_PATH):
    rules = read_json(path)
    required = {"review_ratio", "priority_weight", "normal_weight",
                "default_max_session_minutes", "min_allowed_session_minutes",
                "max_allowed_session_minutes", "recommended_min_content_minutes_per_topic",
                "break_minutes"}
    if not isinstance(rules, dict) or set(rules) != required:
        raise InputError("study_rules.json debe contener exactamente las reglas documentadas.")
    for key, value in rules.items():
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise InputError(f"Regla inválida: {key} debe ser un número positivo finito.")
        if key.endswith("minutes") or key.endswith("per_topic"):
            if type(value) is not int:
                raise InputError(f"Regla inválida: {key} debe ser un entero.")
    if not 0 < rules["review_ratio"] < 1:
        raise InputError("review_ratio debe estar entre 0 y 1, sin incluir los extremos.")
    if rules["priority_weight"] <= rules["normal_weight"]:
        raise InputError("priority_weight debe superar normal_weight.")
    if not (rules["break_minutes"] < rules["min_allowed_session_minutes"]
            <= rules["default_max_session_minutes"] <= rules["max_allowed_session_minutes"]):
        raise InputError("Límites de sesión o descanso incoherentes en las reglas.")
    return rules


def clean_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{field} debe ser un texto no vacío.")
    if any(ord(char) < 32 for char in value):
        raise InputError(f"{field} no debe contener saltos de línea ni caracteres de control.")
    return value.strip()


def validate_data(data, rules=None, today=None):
    rules = load_rules() if rules is None else rules
    today = date.today() if today is None else today
    if not isinstance(data, dict):
        raise InputError("La entrada debe ser un objeto JSON.")
    required = {"subject", "exam_date", "topics", "availability"}
    allowed = required | {"priority_topics", "max_session_minutes"}
    if required - data.keys():
        raise InputError("Faltan campos: " + ", ".join(sorted(required - data.keys())))
    if data.keys() - allowed:
        raise InputError("Campos no admitidos: " + ", ".join(sorted(data.keys() - allowed)))
    subject = clean_text(data["subject"], "subject")
    exam = parse_date(data["exam_date"], "exam_date")
    if exam <= today:
        raise InputError("La fecha del examen debe ser posterior a la fecha actual.")
    if not isinstance(data["topics"], list) or not data["topics"]:
        raise InputError("topics debe ser una lista no vacía.")
    topics = [clean_text(topic, "tema") for topic in data["topics"]]
    if len({topic.casefold() for topic in topics}) != len(topics):
        raise InputError("Hay temas duplicados (se ignoran mayúsculas y espacios exteriores).")
    priorities = data.get("priority_topics", [])
    if not isinstance(priorities, list):
        raise InputError("priority_topics debe ser una lista.")
    priorities = [clean_text(topic, "prioridad") for topic in priorities]
    if len(set(priorities)) != len(priorities):
        raise InputError("Hay prioridades duplicadas.")
    if any(topic not in topics for topic in priorities):
        raise InputError("Cada prioridad debe existir exactamente en topics.")
    maximum = data.get("max_session_minutes", rules["default_max_session_minutes"])
    low, high = rules["min_allowed_session_minutes"], rules["max_allowed_session_minutes"]
    if type(maximum) is not int or not low <= maximum <= high:
        raise InputError(f"max_session_minutes debe ser un entero entre {low} y {high}.")
    availability = data["availability"]
    if not isinstance(availability, dict) or not availability:
        raise InputError("availability debe ser un objeto no vacío.")
    for day, minutes in availability.items():
        parsed = parse_date(day, "availability")
        if parsed < today:
            raise InputError(f"La disponibilidad {day} está en el pasado.")
        if parsed >= exam:
            raise InputError("No se admite disponibilidad el día del examen ni después.")
        if type(minutes) is not int or not 0 < minutes <= 1440:
            raise InputError(f"Los minutos de {day} deben ser enteros entre 1 y 1440.")
    return {"subject": subject, "exam_date": exam.isoformat(), "topics": topics,
            "priority_topics": priorities, "max_session_minutes": maximum,
            "availability": dict(sorted(availability.items()))}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validar una entrada de plan de estudio.")
    parser.add_argument("input", type=Path)
    args = parser.parse_args(argv)
    try:
        validate_data(read_json(args.input))
    except InputError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    print("[OK] Entrada válida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
