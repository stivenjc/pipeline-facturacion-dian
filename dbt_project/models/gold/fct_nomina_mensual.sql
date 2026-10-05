select
    date_trunc(fecha_emision, month)  as periodo,
    count(*)                          as documentos,
    count(distinct nit_receptor)      as empleados,
    sum(total)                        as total_nomina
from {{ ref('slv_documentos_clasificados') }}
where categoria = 'nomina'
group by periodo
