with fuente as (select *
                from {{ source('bronze', 'facturacion_dian') }}),

     tipado as (select cufe_cude,
                       tipo_de_documento,
                       grupo,
                       estado,
                       prefijo,
                       folio,

                       parse_date('%d-%m-%Y', fecha_emision)                      as fecha_emision,
                       safe.parse_timestamp('%Y-%m-%dT%H:%M:%S', fecha_recepcion) as fecha_recepcion,
                       periodo,

                       divisa,
                       forma_de_pago,
                       medio_de_pago,

                       nit_emisor,
                       nombre_emisor,
                       nit_receptor,
                       nombre_receptor,

                       cast(total as numeric)                                     as total,
                       cast(iva as numeric)                                       as iva,
                       cast(inc as numeric)                                       as inc,
                       cast(ic as numeric)                                        as ic,
                       cast(inc_bolsas as numeric)                                as inc_bolsas,
                       cast(ica as numeric)                                       as ica,
                       cast(rete_iva as numeric)                                  as rete_iva,
                       cast(rete_renta as numeric)                                as rete_renta,
                       cast(rete_ica as numeric)                                  as rete_ica,

                       _archivo_origen,
                       _fecha_carga

                from fuente),

     con_orden as (select *,
                          row_number() over (
            partition by cufe_cude
            order by _fecha_carga desc
        ) as fila
                   from tipado)

select *
except
(fila)
from con_orden
where fila = 1
