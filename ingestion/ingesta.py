"""Ingesta de facturación DIAN: Excel -> Parquet por mes (capa bronze).

Uso:
    python ingestion/ingesta.py data/raw/FACTURACION_ENE_A_AGO_2026.xlsx

Qué hace:
    1. Lee el Excel sin alterar los valores.
    2. Valida que las columnas sean las esperadas (si cambian, falla con aviso).
    3. Renombra columnas a snake_case sin tildes (cambio mecánico, no de valores).
    4. Agrega metadatos de carga (archivo de origen y momento de carga).
    5. Escribe un archivo por mes en data/bronze/anio=AAAA/mes=MM/.

Idempotente: ejecutarlo dos veces produce exactamente el mismo resultado,
porque cada mes se REEMPLAZA completo en lugar de agregar filas.
La limpieza de tipos y las reglas de negocio van después, en dbt (silver).
"""
import logging
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SALIDA = Path("data/bronze")
COLUMNA_FECHA = "Fecha Emisión"
FORMATO_FECHA = "%d-%m-%Y"

# Contrato de datos: las 32 columnas que entrega la exportación de la DIAN.
COLUMNAS_ESPERADAS = [
    "Tipo de documento", "CUFE/CUDE", "Folio", "Prefijo", "Divisa", "Forma de Pago",
    "Medio de Pago", "Fecha Emisión", "Fecha Recepción", "NIT Emisor", "Nombre Emisor",
    "NIT Receptor", "Nombre Receptor", "IVA", "ICA", "IC", "INC", "Timbre", "INC Bolsas",
    "IN Carbono", "IN Combustibles", "IC Datos", "ICL", "INPP", "IBUA", "ICUI",
    "Rete IVA", "Rete Renta", "Rete ICA", "Total", "Estado", "Grupo",
]

# Identificadores y códigos: se leen como texto para no perder información.
COLUMNAS_TEXTO = [
    "Folio", "Prefijo", "Medio de Pago", "Forma de Pago", "NIT Emisor", "NIT Receptor",
]


def a_snake_case(nombre: str) -> str:
    """'Fecha Emisión' -> 'fecha_emision'; 'CUFE/CUDE' -> 'cufe_cude'."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")


def leer_excel(ruta: Path) -> pd.DataFrame:
    df = pd.read_excel(ruta, dtype={c: str for c in COLUMNAS_TEXTO})
    faltan = set(COLUMNAS_ESPERADAS) - set(df.columns)
    sobran = set(df.columns) - set(COLUMNAS_ESPERADAS)
    if faltan or sobran:
        raise ValueError(f"El archivo no cumple el contrato. Faltan: {faltan}. Sobran: {sobran}")
    return df


def preparar(df: pd.DataFrame, archivo: str) -> pd.DataFrame:
    # Año y mes solo sirven para decidir en qué carpeta cae cada fila.
    fecha = pd.to_datetime(df[COLUMNA_FECHA], format=FORMATO_FECHA, errors="raise")
    particion = pd.DataFrame({"anio": fecha.dt.year, "mes": fecha.dt.month})

    df = df.rename(columns={c: a_snake_case(c) for c in df.columns})
    df["_archivo_origen"] = archivo
    df["_fecha_carga"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return pd.concat([df, particion], axis=1)


def escribir_por_mes(df: pd.DataFrame) -> None:
    for (anio, mes), grupo in df.groupby(["anio", "mes"]):
        carpeta = SALIDA / f"anio={anio}" / f"mes={mes:02d}"
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / "facturacion.parquet"
        # Sobrescribe: así la carga es idempotente.
        grupo.drop(columns=["anio", "mes"]).to_parquet(destino, index=False)
        log.info("%s -> %d filas", destino, len(grupo))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Uso: python ingestion/ingesta.py <ruta_al_xlsx>")
    ruta = Path(sys.argv[1])
    if not ruta.exists():
        sys.exit(f"No existe el archivo: {ruta}")

    df = leer_excel(ruta)
    log.info("Leídas %d filas de %s", len(df), ruta.name)
    df = preparar(df, ruta.name)
    escribir_por_mes(df)
    log.info("Ingesta terminada: %d filas escritas", len(df))


if __name__ == "__main__":
    main()