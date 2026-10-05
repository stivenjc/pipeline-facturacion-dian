select
    d.*,
    c.categoria,
    c.signo,
    d.total - d.iva               as base_sin_iva,
    c.signo * (d.total - d.iva)   as base_neta,
    c.signo * d.iva               as iva_neto
from {{ ref('slv_documentos') }} as d
left join {{ ref('categoria_documento') }} as c
    on  d.grupo = c.grupo
    and d.tipo_de_documento = c.tipo_de_documento
