"""Carga los Parquet de data/bronze a BigQuery (dataset bronze).

Uso (con el entorno virtual activado y .env configurado):
    python ingestion/cargar_bronze.py

Variables en .env:
    GCP_PROJECT_ID   id del proyecto de Google Cloud
    GCP_LOCATION     ubicación de los datasets (ej. us-central1)
    ANON_SALT        texto secreto para anonimizar nómina (cualquier cadena larga)

Decisiones de diseño:
    - Tabla particionada por mes sobre la columna `periodo` (fecha de emisión).
    - Idempotente: cada mes se carga con WRITE_TRUNCATE sobre SU partición,
      así recargar un mes reemplaza ese mes y no toca los demás.
    - Datos de nómina: nombre y cédula del empleado se reemplazan por un hash
      ANTES de salir del computador. Los archivos locales no se modifican.
    - Al final compara filas y suma de `total` contra lo local.
"""
import hashlib
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ENTRADA = Path("data/bronze")
TABLA = "facturacion_dian"
TIPO_NOMINA = "Nomina Individual"
CLUSTERING = ["grupo", "tipo_de_documento"]


def leer_parquets() -> pd.DataFrame:
    archivos = sorted(ENTRADA.glob("anio=*/mes=*/*.parquet"))
    if not archivos:
        raise SystemExit("No hay Parquet en data/bronze. Ejecuta primero la ingesta.")
    return pd.concat((pd.read_parquet(a) for a in archivos), ignore_index=True)


def anonimizar_nomina(df: pd.DataFrame, sal: str) -> pd.DataFrame:
    """Reemplaza nombre y cédula de los empleados por un hash estable.

    Estable = el mismo empleado produce siempre el mismo hash, así se puede
    seguir contando empleados distintos sin saber quiénes son.
    """
    def h(valor: str) -> str:
        return hashlib.sha256(f"{sal}|{valor}".encode()).hexdigest()[:16]

    es_nomina = df["tipo_de_documento"] == TIPO_NOMINA
    for col in ["nit_receptor", "nombre_receptor"]:
        df.loc[es_nomina, col] = df.loc[es_nomina, col].map(h)
    log.info("Nómina anonimizada: %d filas", es_nomina.sum())
    return df


def agregar_periodo(df: pd.DataFrame) -> pd.DataFrame:
    """Columna técnica para particionar: primer día del mes de emisión."""
    fecha = pd.to_datetime(df["fecha_emision"], format="%d-%m-%Y", errors="raise")
    df["periodo"] = fecha.dt.to_period("M").dt.to_timestamp().dt.date
    return df


def construir_esquema(df: pd.DataFrame) -> list[bigquery.SchemaField]:
    """Esquema explícito: evita que BigQuery adivine mal en un mes con columnas vacías."""
    esquema = []
    for col, tipo in df.dtypes.items():
        if col == "periodo":
            bq_tipo = "DATE"
        elif pd.api.types.is_numeric_dtype(tipo):
            # Todo monto como decimal: si el histórico trae centavos en una
            # columna que hoy es entera, la carga no falla.
            bq_tipo = "FLOAT64"
        else:
            bq_tipo = "STRING"
        esquema.append(bigquery.SchemaField(col, bq_tipo))
    return esquema


def crear_tabla(client: bigquery.Client, tabla_id: str, esquema) -> None:
    tabla = bigquery.Table(tabla_id, schema=esquema)
    tabla.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.MONTH, field="periodo"
    )
    tabla.clustering_fields = CLUSTERING
    client.create_table(tabla, exists_ok=True)


def cargar_particiones(client, tabla_id: str, df: pd.DataFrame, esquema) -> None:
    for periodo, grupo in df.groupby("periodo"):
        decorador = f"{tabla_id}${periodo:%Y%m}"
        config = bigquery.LoadJobConfig(
            schema=esquema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        job = client.load_table_from_dataframe(grupo, decorador, job_config=config)
        job.result()
        log.info("Partición %s cargada: %d filas", f"{periodo:%Y-%m}", len(grupo))


def validar(client, tabla_id: str, df: pd.DataFrame) -> None:
    # Tope de bytes: si la consulta fuera a procesar más de 100 MB, falla en vez de cobrar.
    config = bigquery.QueryJobConfig(maximum_bytes_billed=100 * 1024 * 1024)
    sql = f"SELECT COUNT(*) AS filas, ROUND(SUM(total), 2) AS total FROM `{tabla_id}`"
    fila = list(client.query(sql, job_config=config).result())[0]
    esperado_filas, esperado_total = len(df), round(df["total"].sum(), 2)
    log.info("BigQuery: %d filas, total %s", fila.filas, fila.total)
    log.info("Local:    %d filas, total %s", esperado_filas, esperado_total)
    if fila.filas != esperado_filas or abs(fila.total - esperado_total) > 0.01:
        raise SystemExit("VALIDACIÓN FALLÓ: lo cargado no coincide con lo local")
    log.info("Validación OK: filas y total coinciden")


def main() -> None:
    load_dotenv()
    proyecto = os.environ["GCP_PROJECT_ID"]
    ubicacion = os.environ["GCP_LOCATION"]
    sal = os.environ["ANON_SALT"]

    df = leer_parquets()
    df = anonimizar_nomina(df, sal)
    df = agregar_periodo(df)

    client = bigquery.Client(project=proyecto, location=ubicacion)
    tabla_id = f"{proyecto}.bronze.{TABLA}"
    esquema = construir_esquema(df)

    crear_tabla(client, tabla_id, esquema)
    cargar_particiones(client, tabla_id, df, esquema)
    validar(client, tabla_id, df)


if __name__ == "__main__":
    main()