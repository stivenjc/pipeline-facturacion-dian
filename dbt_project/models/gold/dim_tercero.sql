with contrapartes as (

    -- La contraparte es la otra empresa del documento, no la nuestra
    select case when grupo = 'Emitido' then nit_receptor else nit_emisor end       as nit,
           case when grupo = 'Emitido' then nombre_receptor else nombre_emisor end as nombre,
           categoria
    from {{ ref('slv_documentos_clasificados') }}
    where categoria in ('venta', 'compra', 'pago_prestadores')),

     nombres as (select nit, nombre, count(*) as veces
                 from contrapartes
                 group by nit, nombre),

     nombre_elegido as (

         -- Si un NIT tiene varios nombres, gana el que más se repite
         select nit,
                nombre,
                row_number() over (partition by nit order by veces desc, nombre) as orden, count(*) over (partition by nit)                             as variantes_nombre
         from nombres),

     roles as (select nit,
                      logical_or(categoria = 'venta')            as es_cliente,
                      logical_or(categoria = 'compra')           as es_proveedor,
                      logical_or(categoria = 'pago_prestadores') as es_prestador
               from contrapartes
               group by nit)

select n.nit,
       n.nombre,
       n.variantes_nombre,
       r.es_cliente,
       r.es_proveedor,
       r.es_prestador
from nombre_elegido as n
         join roles as r
              on n.nit = r.nit
where n.orden = 1
