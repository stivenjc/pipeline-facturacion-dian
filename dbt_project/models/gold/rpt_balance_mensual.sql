-- Ingresos, gastos y resultado por mes. Una fila por mes.
-- Solo con documentos de la DIAN: no es utilidad contable.
with documentos as (

    select
        date_trunc(fecha_emision, month)                          as periodo,
        sum(if(categoria = 'venta',            base_neta, 0))     as ingresos_ventas,
        sum(if(categoria = 'compra',           base_neta, 0))     as compras,
        sum(if(categoria = 'pago_prestadores', base_neta, 0))     as prestadores
    from {{ ref('fct_documentos') }}
    group by periodo

),

nomina as (

    select periodo, total_nomina as nomina
    from {{ ref('fct_nomina_mensual') }}

),

unidos as (

    -- full outer join: un mes con solo nómina o solo documentos no se pierde
    select
        coalesce(d.periodo, n.periodo)    as periodo,
        coalesce(d.ingresos_ventas, 0)    as ingresos_ventas,
        coalesce(d.compras, 0)            as compras,
        coalesce(d.prestadores, 0)        as prestadores,
        coalesce(n.nomina, 0)             as nomina
    from documentos as d
    full outer join nomina as n
        on d.periodo = n.periodo

)

select
    u.periodo,
    f.anio_mes,
    f.nombre_mes,
    u.ingresos_ventas,
    u.compras,
    u.prestadores,
    u.nomina,
    u.compras + u.prestadores + u.nomina                       as gastos_totales,
    u.ingresos_ventas - (u.compras + u.prestadores + u.nomina) as resultado
from unidos as u
left join {{ ref('dim_fecha') }} as f
    on u.periodo = f.fecha