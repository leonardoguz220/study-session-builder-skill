"""Demostración reproducible con fechas relativas al día de ejecución."""

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


def main():
    scripts = Path(__file__).resolve().parent
    output = Path.cwd() / "output"
    today = date.today()

    data = {
        "subject": "Aplicaciones con Redes",
        "exam_date": (today + timedelta(days=5)).isoformat(),
        "topics": [
            "TLS 1.3",
            "DNS y DHCP",
            "HTTP/2 y HTTP/3",
            "Balanceo de carga",
        ],
        "priority_topics": [
            "TLS 1.3",
            "Balanceo de carga",
        ],
        "availability": {
            (today + timedelta(days=i)).isoformat(): minutes
            for i, minutes in enumerate([120, 90, 180, 120, 120])
        },
        "max_session_minutes": 50,
    }

    try:
        output.mkdir(parents=True, exist_ok=True)

        valid = output / "demo-valid.json"
        invalid = output / "demo-invalid.json"

        valid.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        invalid.write_text(
            json.dumps(
                {
                    **data,
                    "priority_topics": ["Tema inexistente"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        steps = [
            (
                ["validate_input.py", str(valid)],
                0,
                "[OK]",
            ),
            (
                [
                    "build_schedule.py",
                    str(valid),
                    "--output",
                    str(output / "study-plan.md"),
                ],
                0,
                "[OK]",
            ),
            (
                [
                    "build_schedule.py",
                    str(invalid),
                    "--output",
                    str(output / "invalid-plan.md"),
                ],
                2,
                "[ERROR]",
            ),
        ]

        for args, expected, marker in steps:
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(scripts / args[0]),
                    *args[1:],
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            combined = (result.stdout or "") + (result.stderr or "")

            print(combined.strip())

            if (
                result.returncode != expected
                or marker not in combined
                or "Traceback" in combined
            ):
                print("[ERROR] Resultado inesperado en la demo.")
                return 1

        if not (output / "study-plan.md").is_file():
            print("[ERROR] No se generó el archivo del plan.")
            return 1

    except (OSError, UnicodeError) as exc:
        print(
            f"[ERROR] No se pudo completar la demo: {exc}",
            file=sys.stderr,
        )
        return 1

    print("DEMO COMPLETA: ambos casos se comportaron como se esperaba.")
    return 0


if __name__ == "__main__":
    sys.exit(main())