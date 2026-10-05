select
    cufe_cude,
    fecha_emision,
    case when grupo = 'Emitido' then nit_receptor else nit_emisor end as nit_tercero,
    categoria,
    tipo_de_documento,
    prefijo,
    folio,
    signo,
    base_sin_iva,
    base_neta,
    iva_neto,
    signo * total as total_neto
from {{ ref('slv_documentos_clasificados') }}
where categoria in ('venta', 'compra', 'pago_prestadores')
