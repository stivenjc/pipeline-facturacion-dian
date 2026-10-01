# Reporte de calidad de datos

## 1. Forma general
- Filas: 1,237
- Columnas: 32

## 2. Unicidad
- Duplicados en `CUFE/CUDE`: 0
- Duplicados en (Prefijo, Folio): 0

## 3. Nulos por columna
- Prefijo: 220 (17.8%)
- Divisa: 272 (22.0%)
- Forma de Pago: 272 (22.0%)
- Medio de Pago: 272 (22.0%)

## 4. Tipos de documento
- Factura electrónica: 934 filas, total 960,449,464
- Application response: 209 filas, total 0
- Nomina Individual: 63 filas, total 205,476,100
- Documento soporte con no obligados: 14 filas, total 24,616,464
- Nota de crédito electrónica: 14 filas, total 33,411,272
- Documento equivalente - Transporte aéreo de pasajeros: 1 filas, total 1,714,490
- Documento equivalente POS: 1 filas, total 68,000
- Factura electrónica de contingencia: 1 filas, total 48,500

Emitido vs Recibido:
- Emitido: 625
- Recibido: 612

## 5. ¿Quién tiene prefijo nulo?
- Application response: 209
- Nota de crédito electrónica: 10
- Documento equivalente - Transporte aéreo de pasajeros: 1

## 6. Fechas
- Fecha Emisión: 2026-01-02 a 2026-08-31, no interpretables: 0

Documentos por mes:
- 2026-01: 148
- 2026-02: 158
- 2026-03: 145
- 2026-04: 210
- 2026-05: 166
- 2026-06: 124
- 2026-07: 128
- 2026-08: 158

## 7. Valores atípicos en Total (> Q3 + 3*IQR de facturas)
- Umbral: 2,188,606  |  Documentos por encima: 126
- Factura electrónica | Recibido | 30-07-2026 | SUMINISTROS DIGITALES SAS -> PER PRINT DIGITAL SAS | 110,000,000
- Factura electrónica | Emitido | 29-04-2026 | PER PRINT AVISAI DIGITAL S A S -> BALOON AGENCIA CREATIVA S.A.S. | 63,214,406
- Factura electrónica | Recibido | 23-04-2026 | FACTORY PROYECTOS COMERCIALES SAS -> PER PRINT AVISAI DIGITAL | 60,482,208
- Factura electrónica | Emitido | 09-03-2026 | PER PRINT AVISAI DIGITAL S A S -> UNIVERSIDAD DE LA SABANA | 41,005,020
- Factura electrónica | Recibido | 28-03-2026 | FACTORY PROYECTOS COMERCIALES SAS -> PER PRINT AVISAI DIGITAL | 36,115,381

## 8. Totales en cero (excluyendo Application response)
- Filas: 0
