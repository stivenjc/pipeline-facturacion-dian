with limites as (

    -- Del 1 de enero del año más antiguo al 31 de diciembre del más reciente
    select date_trunc(min(fecha_emision), year) as inicio,
           date_sub(
                   date_add(date_trunc(max(fecha_emision), year), interval 1 year),
                   interval 1 day
        )           as fin
    from {{ ref('slv_documentos_clasificados') }}),

     dias as (select fecha
              from limites,
                   unnest(generate_date_array(inicio, fin)) as fecha)

select fecha,
       extract(year from fecha)    as anio,
       extract(quarter from fecha) as trimestre,
       extract(month from fecha)   as mes,
       format_date('%Y-%m', fecha) as anio_mes,
       date_trunc(fecha, month)    as periodo, ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    [
offset(extract(month from fecha) - 1)] as nombre_mes, ['domingo','lunes','martes','miércoles','jueves','viernes','sábado'] [offset(extract(dayofweek from fecha) - 1)] as dia_semana, extract(dayofweek from fecha) in (1, 7) as es_fin_de_semana

from dias
