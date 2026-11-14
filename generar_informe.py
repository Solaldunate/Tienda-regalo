import os
import subprocess
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

AUTOR = "Soledad"
COLUMNAS = ["Quantity", "UnitPrice"]
MESES = {"control": "octubre", "nuevo": "noviembre"}
UMBRAL = 0.1


def obtener_commit():
    commit = os.environ.get("GITHUB_SHA")
    if commit:
        return commit

    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return "Vista local · commit no disponible"

    if resultado.returncode == 0:
        return f"Vista local · HEAD {resultado.stdout.strip()}"

    return "Vista local · todavía sin commit"


def main():
    referencia = pd.read_csv(
        "datos/referencia.csv",
        encoding="utf-8-sig",
        usecols=COLUMNAS,
    )
    actual = pd.read_csv(
        "datos/actual.csv",
        encoding="utf-8-sig",
        usecols=[*COLUMNAS, "lote"],
    )

    mes = MESES[actual["lote"].iloc[0]]
    definicion = DataDefinition(numerical_columns=COLUMNAS)
    datos_referencia = Dataset.from_pandas(referencia[COLUMNAS], definicion)
    datos_actuales = Dataset.from_pandas(actual[COLUMNAS], definicion)

    reporte = Report([
        DataDriftPreset(
            columns=COLUMNAS,
            num_method="wasserstein",
            num_threshold=UMBRAL,
            include_tests=False,
        ),
    ])
    resultado = reporte.run(
        current_data=datos_actuales,
        reference_data=datos_referencia,
    )

    sitio = Path("sitio")
    sitio.mkdir(exist_ok=True)
    resultado.save_html(str(sitio / "informe.html"))

    cantidad = actual["Quantity"].median()
    precio = actual["UnitPrice"].median()
    filas = f"{len(actual):,}".replace(",", ".")
    generado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit = escape(obtener_commit())

    portada = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Monitoreo de ventas de regalos</title>
  <style>
    body {{
      max-width: 48rem;
      margin: 3rem auto;
      padding: 0 1.25rem;
      background: #f5f7fa;
      color: #17243a;
      font: 1rem/1.6 system-ui, sans-serif;
    }}
    main {{
      background: white;
      padding: 1.5rem;
      border: 1px solid #d9e0e8;
      border-radius: 0.75rem;
    }}
    a {{ color: #174f9e; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <main>
    <h1>Monitoreo de ventas de regalos</h1>
    <h2>Último lote publicado</h2>
    <ul>
      <li><strong>Mes:</strong> {mes.capitalize()} de 2011</li>
      <li><strong>Filas analizadas:</strong> {filas}</li>
      <li><strong>Mediana de unidades por fila:</strong> {cantidad:g}</li>
      <li><strong>Mediana de precio unitario:</strong> £{precio:.2f} GBP</li>
    </ul>
    <p><a href="informe.html">Comparar {mes} con septiembre</a></p>
    <p><strong>Autor:</strong> {escape(AUTOR)}</p>
    <p><strong>Fuente:</strong>
      <a href="https://doi.org/10.24432/C5BW33">Online Retail, UCI</a>
    </p>
    <p><strong>Fecha de generación:</strong> {generado}</p>
    <p><strong>Commit:</strong> <code>{commit}</code></p>
  </main>
</body>
</html>
"""
    (sitio / "index.html").write_text(portada, encoding="utf-8")

    print(f"Comparación generada: {mes} frente a septiembre de 2011")
    print("Archivos: sitio/index.html y sitio/informe.html")


if __name__ == "__main__":
    main()