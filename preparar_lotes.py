import csv
import shutil
from pathlib import Path

carpeta = Path("datos")
origen = carpeta / "ventas_regalos_2011.csv"
lotes = {"referencia": [], "control": [], "nuevo": []}

with origen.open(encoding="utf-8-sig", newline="") as archivo:
    lector = csv.DictReader(archivo)
    columnas = lector.fieldnames
    if columnas is None or "lote" not in columnas:
        raise SystemExit("Falta la columna lote.")

    for fila in lector:
        nombre = fila["lote"]
        if nombre not in lotes:
            raise SystemExit(f"Lote inesperado: {nombre!r}")
        lotes[nombre].append(fila)

for nombre, filas in lotes.items():
    if len(filas) != 12_000:
        raise SystemExit(f"{nombre}: se esperaban 12000 filas, hay {len(filas)}.")

carpeta.mkdir(exist_ok=True)

for nombre, filas in lotes.items():
    ruta = carpeta / f"{nombre}.csv"
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"{ruta}: {len(filas)} filas de datos")

actual = carpeta / "actual.csv"
if actual.exists():
    print(f"{actual} ya existe. Se conservó su contenido.")
else:
    shutil.copyfile(carpeta / "control.csv", actual)
    print(f"{actual}: copia inicial de octubre")