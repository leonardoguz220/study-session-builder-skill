"""Distribuir minutos enteros y renderizar un plan con la plantilla incluida."""

import argparse
import re
import sys
from fractions import Fraction
from pathlib import Path

from validate_input import InputError, SKILL_DIR, load_rules, read_json, validate_data

TEMPLATE_PATH = SKILL_DIR / "assets" / "study-plan-template.md"


def allocate_minutes(total, weights):
    """Método de restos mayores: conservar cada minuto sin sesgos por float."""
    weights = [Fraction(str(weight)) for weight in weights]
    quotas = [total * weight / sum(weights) for weight in weights]
    result = [int(quota) for quota in quotas]
    order = sorted(range(len(weights)), key=lambda i: (-(quotas[i] - result[i]), i))
    for i in order[:total - sum(result)]:
        result[i] += 1
    return result


def build_schedule(data, rules=None, today=None):
    rules = load_rules() if rules is None else rules
    data = validate_data(data, rules, today)
    maximum, pause = data["max_session_minutes"], rules["break_minutes"]
    days = []
    for day, available in data["availability"].items():
        # Mínimo número de sesiones que permite incluir descansos en el presupuesto.
        count = (available + pause + maximum + pause - 1) // (maximum + pause)
        study = available - (count - 1) * pause
        lengths = allocate_minutes(study, [1] * count)
        days.append({"date": day, "available": available, "break_minutes": (count - 1) * pause,
                     "sessions": [{"minutes": length, "activities": []} for length in lengths]})
    total = sum(data["availability"].values())
    breaks = sum(day["break_minutes"] for day in days)
    study = total - breaks
    review = min(study - 1, max(1, int(study * Fraction(str(rules["review_ratio"])))))
    content = study - review
    priorities = set(data["priority_topics"])
    weights = [rules["priority_weight"] if topic in priorities else rules["normal_weight"]
               for topic in data["topics"]]
    amounts = allocate_minutes(content, weights)
    queue = [{"kind": "content", "topic": topic, "minutes": minutes}
             for topic, minutes in zip(data["topics"], amounts) if minutes]
    if review:
        queue.append({"kind": "review", "topic": "Repaso general", "minutes": review})
    position = 0
    remaining = queue[0]["minutes"]
    for day in days:
        for session in day["sessions"]:
            room = session["minutes"]
            while room:
                take = min(room, remaining)
                session["activities"].append({**queue[position], "minutes": take})
                room -= take
                remaining -= take
                if remaining == 0:
                    position += 1
                    if position < len(queue):
                        remaining = queue[position]["minutes"]
    warnings = []
    minimum = rules["recommended_min_content_minutes_per_topic"]
    scarce = [topic for topic, minutes in zip(data["topics"], amounts) if minutes < minimum]
    if scarce:
        warnings.append(f"Poco tiempo: estos temas reciben menos de {minimum} min de contenido: "
                        + ", ".join(scarce) + ". Considera ampliar tu disponibilidad.")
    if not review:
        warnings.append("No alcanza el tiempo para reservar un minuto de repaso.")
    if any(minutes == 0 for minutes in amounts):
        warnings.append("Uno o más temas quedan sin tiempo asignado; el plan no cubre todos los temas.")
    return {"input": data, "days": days, "total_minutes": total, "break_minutes": breaks,
            "study_minutes": study, "review_minutes": review, "content_minutes": content,
            "topic_minutes": dict(zip(data["topics"], amounts)), "warnings": warnings,
            "pause": pause}


def escape_markdown(value):
    return re.sub(r"([\\`*_{}\[\]()#+.!|<>~-])", r"\\\1", str(value))


def render_plan(plan, template_path=TEMPLATE_PATH):
    try:
        template = Path(template_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InputError("No se pudo leer la plantilla del plan.") from exc
    daily = []
    for day in plan["days"]:
        daily.extend([f"### {day['date']} — {day['available']} min disponibles", "",
                      "| Sesión | Actividades | Estudio |", "| --- | --- | ---: |"])
        for number, session in enumerate(day["sessions"], 1):
            activities = "; ".join(f"{escape_markdown(item['topic'])} ({item['minutes']} min)"
                                   for item in session["activities"])
            daily.append(f"| {number} | {activities} | {session['minutes']} min |")
        daily.extend(["", f"Descansos sugeridos: {plan['pause']} min entre sesiones "
                      f"({day['break_minutes']} min en total, incluidos en la disponibilidad).", ""])
    summary = ["| Tema | Prioridad explícita | Contenido |", "| --- | --- | ---: |"]
    for topic, minutes in plan["topic_minutes"].items():
        priority = "Sí" if topic in plan["input"]["priority_topics"] else "No"
        summary.append(f"| {escape_markdown(topic)} | {priority} | {minutes} min |")
    values = {"SUBJECT": escape_markdown(plan["input"]["subject"]),
              "EXAM_DATE": plan["input"]["exam_date"], "TOTAL_TIME": str(plan["total_minutes"]),
              "MAX_SESSION": str(plan["input"]["max_session_minutes"]),
              "STATUS": "Con advertencias" if plan["warnings"] else "Plan generado",
              "WARNINGS": "\n".join("- " + escape_markdown(w) for w in plan["warnings"])
                          or "Sin advertencias de tiempo.",
              "DAILY_PLAN": "\n".join(daily), "TOPIC_SUMMARY": "\n".join(summary),
              "CONTENT_TIME": str(plan["content_minutes"]),
              "REVIEW_TIME": str(plan["review_minutes"]), "BREAK_TIME": str(plan["break_minutes"])}
    placeholders = set(re.findall(r"\{\{([A-Z_]+)\}\}", template))
    if placeholders != set(values):
        raise InputError("La plantilla debe conservar todas las variables documentadas, sin agregar otras.")
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: values[match[1]], template)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generar un plan Markdown antes del examen.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/study-plan.md"))
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise InputError("La salida no puede sobrescribir el archivo de entrada.")
        plan = build_schedule(read_json(args.input))
        text = render_plan(plan)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    except InputError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except OSError:
        print("[ERROR] No se pudo guardar el plan en la ruta indicada.", file=sys.stderr)
        return 1
    print(f"[OK] Plan generado: {args.output}")
    print(f"Tiempo: {plan['content_minutes']} min contenido + {plan['review_minutes']} min repaso "
          f"+ {plan['break_minutes']} min descansos = {plan['total_minutes']} min.")
    for warning in plan["warnings"]:
        print(f"[AVISO] {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
