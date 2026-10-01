"""Perfilado de calidad del archivo de facturación electrónica (DIAN).

Uso:
    python ingestion/perfilado.py data/raw/FACTURACION_ENE_A_AGO_2026.xlsx

Genera un reporte en consola y lo guarda en docs/reporte_calidad.md.
No modifica los datos originales: solo los lee.
"""
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

CLAVE_NATURAL = "CUFE/CUDE"
COLUMNAS_FECHA = ["Fecha Emisión"]
FORMATO_FECHA = "%d-%m-%Y"


def cargar(ruta: Path) -> pd.DataFrame:
    # dtype=str en las columnas que son identificadores: evita que pandas
    # convierta 'Folio' u otros códigos en números y pierda ceros a la izquierda.
    return pd.read_excel(ruta, dtype={"Folio": str, "Prefijo": str, "Medio de Pago": str})


def perfilar(df: pd.DataFrame) -> list[str]:
    r: list[str] = []
    r.append("# Reporte de calidad de datos\n")

    # 1. Forma general
    r.append("## 1. Forma general")
    r.append(f"- Filas: {len(df):,}")
    r.append(f"- Columnas: {df.shape[1]}\n")

    # 2. Unicidad de la clave natural
    dup = df[CLAVE_NATURAL].duplicated().sum()
    r.append("## 2. Unicidad")
    r.append(f"- Duplicados en `{CLAVE_NATURAL}`: {dup}")
    r.append(f"- Duplicados en (Prefijo, Folio): {df.duplicated(['Prefijo', 'Folio']).sum()}\n")

    # 3. Nulos por columna
    nulos = df.isna().sum()
    nulos = nulos[nulos > 0]
    r.append("## 3. Nulos por columna")
    if nulos.empty:
        r.append("- Sin nulos")
    for col, n in nulos.items():
        r.append(f"- {col}: {n} ({n / len(df):.1%})")
    r.append("")

    # 4. Composición por tipo de documento y grupo
    r.append("## 4. Tipos de documento")
    resumen = (
        df.groupby("Tipo de documento")["Total"]
        .agg(filas="count", total="sum")
        .sort_values("filas", ascending=False)
    )
    for tipo, fila in resumen.iterrows():
        r.append(f"- {tipo}: {int(fila['filas'])} filas, total {fila['total']:,.0f}")
    r.append("")
    r.append("Emitido vs Recibido:")
    for grupo, n in df["Grupo"].value_counts().items():
        r.append(f"- {grupo}: {n}")
    r.append("")

    # 5. ¿Los nulos tienen explicación de negocio?
    sin_prefijo = df["Prefijo"].isna()
    tipos_sin_prefijo = df.loc[sin_prefijo, "Tipo de documento"].value_counts()
    r.append("## 5. ¿Quién tiene prefijo nulo?")
    for tipo, n in tipos_sin_prefijo.items():
        r.append(f"- {tipo}: {n}")
    r.append("")

    # 6. Fechas
    r.append("## 6. Fechas")
    for col in COLUMNAS_FECHA:
        f = pd.to_datetime(df[col], format=FORMATO_FECHA, errors="coerce")
        r.append(f"- {col}: {f.min().date()} a {f.max().date()}, no interpretables: {f.isna().sum()}")
    mensual = pd.to_datetime(df["Fecha Emisión"], format=FORMATO_FECHA).dt.to_period("M")
    r.append("\nDocumentos por mes:")
    for mes, n in mensual.value_counts().sort_index().items():
        r.append(f"- {mes}: {n}")
    r.append("")

    # 7. Valores atípicos en Total (regla IQR, solo informa, no elimina)
    facturas = df[df["Tipo de documento"] == "Factura electrónica"]["Total"]
    q1, q3 = facturas.quantile([0.25, 0.75])
    limite = q3 + 3 * (q3 - q1)
    atipicos = df[df["Total"] > limite].sort_values("Total", ascending=False)
    r.append("## 7. Valores atípicos en Total (> Q3 + 3*IQR de facturas)")
    r.append(f"- Umbral: {limite:,.0f}  |  Documentos por encima: {len(atipicos)}")
    for _, f in atipicos.head(5).iterrows():
        r.append(
            f"- {f['Tipo de documento']} | {f['Grupo']} | {f['Fecha Emisión']} | "
            f"{f['Nombre Emisor']} -> {f['Nombre Receptor']} | {f['Total']:,.0f}"
        )
    r.append("")

    # 8. Totales en cero fuera de los eventos
    ceros = df[(df["Total"] == 0) & (df["Tipo de documento"] != "Application response")]
    r.append("## 8. Totales en cero (excluyendo Application response)")
    r.append(f"- Filas: {len(ceros)}\n")

    return r


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Uso: python ingestion/perfilado.py <ruta_al_xlsx>")
    ruta = Path(sys.argv[1])
    if not ruta.exists():
        sys.exit(f"No existe el archivo: {ruta}")

    df = cargar(ruta)
    reporte = perfilar(df)
    for linea in reporte:
        log.info(linea)

    salida = Path("docs/reporte_calidad.md")
    salida.parent.mkdir(exist_ok=True)
    salida.write_text("\n".join(reporte), encoding="utf-8")
    log.info(f"Reporte guardado en {salida}")


if __name__ == "__main__":
    main()
