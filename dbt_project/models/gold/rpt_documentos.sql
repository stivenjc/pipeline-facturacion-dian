-- Capa de reporte: una tabla ancha para el dashboard, una fila por documento.
-- Looker Studio solo suma y filtra; no aplica reglas de negocio.
select
    f.cufe_cude,
    f.fecha_emision,
    d.periodo,
    d.anio_mes,
    d.nombre_mes,
    f.categoria,
    c.etiqueta                 as categoria_nombre,
    c.tipo_flujo,
    c.orden                    as categoria_orden,
    f.nit_tercero,
    t.nombre                   as tercero,
    f.tipo_de_documento,
    f.prefijo,
    f.folio,
    f.base_neta,
    f.iva_neto,
    f.total_neto,

    -- Una columna por concepto: cada gráfico suma una sola
    if(f.categoria = 'venta',            f.base_neta, 0) as ventas_netas,
    if(f.categoria = 'compra',           f.base_neta, 0) as compras_netas,
    if(f.categoria = 'pago_prestadores', f.base_neta, 0) as pagos_prestadores,
    if(f.categoria = 'venta',            f.iva_neto,  0) as iva_generado,
    if(f.categoria = 'compra',           f.iva_neto,  0) as iva_descontable

from {{ ref('fct_documentos') }} as f
left join {{ ref('dim_fecha') }}     as d on f.fecha_emision = d.fecha
left join {{ ref('dim_categoria') }} as c on f.categoria     = c.categoria
left join {{ ref('dim_tercero') }}   as t on f.nit_tercero   = t.nit
