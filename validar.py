import csv
import math
import re
from datetime import datetime
from pathlib import Path

COLUMNAS = {
    "InvoiceNo", "StockCode", "Description", "InvoiceDate",
    "Quantity", "UnitPrice", "lote",
}

MESES = {
    "referencia": (2011, 9),
    "control": (2011, 10),
    "nuevo": (2011, 11),
}

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def validar_csv(ruta, lotes_permitidos):
    def error(campo, motivo):
        return ValueError(f"{ruta} | fila {numero} | {campo}: {motivo}")

    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo, strict=True)
        encabezados = lector.fieldnames or []
        numero = 1

        if len(encabezados) != len(COLUMNAS) or set(encabezados) != COLUMNAS:
            raise error("encabezado", "se requieren las siete columnas del trabajo")

        total = 0
        lote_archivo = None

        for numero, fila in enumerate(lector, start=2):
            if None in fila or any(valor is None for valor in fila.values()):
                raise error("columnas", "la fila debe tener siete valores")

            for campo in ("InvoiceNo", "StockCode", "Description"):
                if not fila[campo].strip():
                    raise error(campo, "el campo está vacío")

            lote = fila["lote"]
            if lote not in lotes_permitidos:
                raise error("lote", f"lote no permitido: {lote!r}")
            if lote_archivo is None:
                lote_archivo = lote
            if lote != lote_archivo:
                raise error("lote", "el archivo contiene más de un lote")

            texto_fecha = fila["InvoiceDate"]
            try:
                fecha = datetime.strptime(texto_fecha, FORMATO_FECHA)
            except ValueError:
                raise error("InvoiceDate", f"fecha u hora inválida: {texto_fecha!r}") from None

            if fecha.strftime(FORMATO_FECHA) != texto_fecha:
                raise error("InvoiceDate", "usa el formato AAAA-MM-DD HH:MM:SS")
            if (fecha.year, fecha.month) != MESES[lote]:
                raise error("InvoiceDate", f"el año y mes deben corresponder al lote {lote}")

            cantidad = fila["Quantity"]
            if not re.fullmatch(r"[0-9]+", cantidad) or int(cantidad) <= 0:
                raise error("Quantity", "debe ser un entero positivo")

            try:
                precio = float(fila["UnitPrice"])
            except ValueError:
                raise error("UnitPrice", "debe ser un número") from None
            if not math.isfinite(precio) or precio <= 0:
                raise error("UnitPrice", "debe ser finito y mayor que cero")

            total += 1

        if total == 0:
            raise error("datos", "el archivo debe contener al menos una fila")

    return total


def main():
    archivos = [
        (Path("datos/referencia.csv"), {"referencia"}),
        (Path("datos/actual.csv"), {"control", "nuevo"}),
    ]

    for ruta, lotes_permitidos in archivos:
        try:
            total = validar_csv(ruta, lotes_permitidos)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise SystemExit(f"ERROR: {ruta} | no se pudo leer el CSV: {exc}") from None
        except ValueError as exc:
            raise SystemExit(f"ERROR: {exc}") from None

        print(f"OK | {ruta} | {total} filas válidas")


if __name__ == "__main__":
    main()