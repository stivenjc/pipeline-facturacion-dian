select
    d.*,
    c.categoria,
    c.signo,
    d.total - d.iva               as base_sin_iva,
    c.signo * (d.total - d.iva)   as base_neta,
    c.signo * d.iva               as iva_neto,

    -- El tercero es la otra empresa del documento, no la nuestra:
    --   emitido  -> a quien se lo emitimos (receptor)
    --   recibido -> quien nos lo emitió (emisor)
    case when d.grupo = 'Emitido' then d.nit_receptor    else d.nit_emisor    end as nit_tercero,
    case when d.grupo = 'Emitido' then d.nombre_receptor else d.nombre_emisor end as nombre_tercero

from {{ ref('slv_documentos') }} as d
left join {{ ref('categoria_documento') }} as c
    on  d.grupo = c.grupo
    and d.tipo_de_documento = c.tipo_de_documento
