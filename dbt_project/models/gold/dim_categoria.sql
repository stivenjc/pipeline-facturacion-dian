select
    categoria,
    etiqueta,
    tipo_flujo,
    orden
from {{ ref('categoria_etiqueta') }}
