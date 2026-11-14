import csv

import pytest

from validar import validar_csv


FILA_VALIDA = {
    "InvoiceNo": "536365",
    "StockCode": "85123A",
    "Description": "WHITE HEART T-LIGHT HOLDER",
    "InvoiceDate": "2011-10-03 09:00:00",
    "Quantity": "6",
    "UnitPrice": "2.55",
    "lote": "control",
}


def escribir_csv(ruta, filas, columnas=None):
    if columnas is None:
        columnas = list(FILA_VALIDA)

    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def test_archivo_valido(tmp_path):
    ruta = tmp_path / "actual.csv"
    escribir_csv(ruta, [FILA_VALIDA])

    assert validar_csv(ruta, {"control", "nuevo"}) == 1


def test_encabezado_faltante(tmp_path):
    ruta = tmp_path / "actual.csv"
    fila = FILA_VALIDA.copy()
    del fila["Description"]
    escribir_csv(ruta, [fila], columnas=list(fila))

    with pytest.raises(ValueError, match=r"fila 1 \| encabezado"):
        validar_csv(ruta, {"control", "nuevo"})


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("InvoiceDate", "2011-10-32 09:00:00"),
        ("Quantity", "2.5"),
        ("UnitPrice", "-1.50"),
    ],
    ids=["fecha-imposible", "cantidad-no-entera", "precio-negativo"],
)
def test_dato_invalido(tmp_path, campo, valor):
    ruta = tmp_path / "actual.csv"
    escribir_csv(ruta, [{**FILA_VALIDA, campo: valor}])

    with pytest.raises(ValueError, match=rf"fila 2 \| {campo}:"):
        validar_csv(ruta, {"control", "nuevo"})


def test_factura_repetida_se_acepta(tmp_path):
    ruta = tmp_path / "actual.csv"
    segundo_producto = {
        **FILA_VALIDA,
        "StockCode": "71053",
        "Description": "WHITE METAL LANTERN",
    }
    escribir_csv(ruta, [FILA_VALIDA, segundo_producto])

    assert validar_csv(ruta, {"control", "nuevo"}) == 2