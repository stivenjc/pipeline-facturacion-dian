-- Capa de reporte: una tabla ancha para el dashboard, una fila por documento.
-- Looker Studio y Power BI solo suman y filtran; no aplican reglas de negocio.
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
    if(f.categoria = 'compra',           f.iva_neto,  0) as iva_descontable,

    -- ¿El cliente compró por primera vez este mes o ya venía comprando?
    case
        when f.categoria <> 'venta' then 'No aplica'
        when date_trunc(f.fecha_emision, month) = t.primer_mes_compra then 'Nuevo'
        else 'Recurrente'
    end as tipo_cliente_mes,

    -- Actividad del cliente (solo en ventas; en compras y prestadores no aplica)
    if(f.categoria = 'venta', t.ultimo_mes_compra, null)     as ultimo_mes_compra,
    if(f.categoria = 'venta', t.meses_sin_comprar, null)     as meses_sin_comprar,
    if(f.categoria = 'venta', t.estado_cliente, 'No aplica') as estado_cliente,

    -- Cómo se pactó el pago y qué tamaño tiene la factura
    coalesce(p.forma_pago, 'Sin dato') as forma_pago,
    f.rango_factura

from {{ ref('fct_documentos') }} as f
left join {{ ref('dim_fecha') }}     as d on f.fecha_emision = d.fecha
left join {{ ref('dim_categoria') }} as c on f.categoria     = c.categoria
left join {{ ref('dim_tercero') }}   as t on f.nit_tercero   = t.nit
left join {{ ref('forma_pago') }}    as p on f.forma_de_pago = p.codigo