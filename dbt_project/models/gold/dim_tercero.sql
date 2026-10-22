with contrapartes as (

    -- El tercero ya viene resuelto desde silver (nit_tercero, nombre_tercero)
    select
        nit_tercero    as nit,
        nombre_tercero as nombre,
        categoria
    from {{ ref('slv_documentos_clasificados') }}
    where categoria in ('venta', 'compra', 'pago_prestadores')

),

nombres as (

    select nit, nombre, count(*) as veces
    from contrapartes
    group by nit, nombre

),

nombre_elegido as (

    -- Si un NIT tiene varios nombres, gana el que más se repite
    select
        nit,
        nombre,
        row_number() over (partition by nit order by veces desc, nombre) as orden,
        count(*)     over (partition by nit)                             as variantes_nombre
    from nombres

),

roles as (

    select
        nit,
        logical_or(categoria = 'venta')            as es_cliente,
        logical_or(categoria = 'compra')           as es_proveedor,
        logical_or(categoria = 'pago_prestadores') as es_prestador
    from contrapartes
    group by nit

),

actividad_clientes as (

    -- Cuándo compra cada cliente. Solo cuentan las facturas de venta:
    -- una nota crédito corrige una compra, no es una compra nueva.
    select
        nit_tercero                                       as nit,
        min(date_trunc(fecha_emision, month))             as primer_mes_compra,
        max(date_trunc(fecha_emision, month))             as ultimo_mes_compra,
        count(distinct date_trunc(fecha_emision, month))  as meses_con_compras
    from {{ ref('slv_documentos_clasificados') }}
    where categoria = 'venta'
      and tipo_de_documento = 'Factura electrónica'
    group by nit_tercero

),

referencia as (

    -- Último mes con datos: contra él se mide cuánto lleva cada cliente sin comprar
    select max(date_trunc(fecha_emision, month)) as mes_referencia
    from {{ ref('slv_documentos_clasificados') }}

)

select
    n.nit,
    n.nombre,
    n.variantes_nombre,
    r.es_cliente,
    r.es_proveedor,
    r.es_prestador,
    a.primer_mes_compra,
    a.ultimo_mes_compra,
    a.meses_con_compras,
    date_diff(ref.mes_referencia, a.ultimo_mes_compra, month) as meses_sin_comprar,
    case
        when a.nit is null then null
        when date_diff(ref.mes_referencia, a.ultimo_mes_compra, month) >= 3 then 'Inactivo'
        else 'Activo'
    end as estado_cliente
from nombre_elegido as n
join roles as r
    on n.nit = r.nit
left join actividad_clientes as a
    on n.nit = a.nit
cross join referencia as ref
where n.orden = 1