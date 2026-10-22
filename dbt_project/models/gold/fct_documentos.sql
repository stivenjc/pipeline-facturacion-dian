select
    cufe_cude,
    fecha_emision,
    nit_tercero,
    categoria,
    tipo_de_documento,
    prefijo,
    folio,
    signo,
    base_sin_iva,
    base_neta,
    iva_neto,
    signo * total as total_neto,

    -- Código DIAN de la forma de pago (1 contado, 2 crédito); se traduce en rpt_documentos
    forma_de_pago,

    -- Tamaño de la factura de venta, sobre el valor sin IVA.
    -- Los números del inicio permiten ordenar los rangos en un gráfico.
    case
        when categoria <> 'venta'
          or tipo_de_documento <> 'Factura electrónica' then 'No aplica'
        when base_sin_iva < 500000    then '1. Menos de 500 mil'
        when base_sin_iva <= 10000000 then '2. De 500 mil a 10 millones'
        else                               '3. Más de 10 millones'
    end as rango_factura

from {{ ref('slv_documentos_clasificados') }}
where categoria in ('venta', 'compra', 'pago_prestadores')