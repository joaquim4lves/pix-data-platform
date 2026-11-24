-- A current key can be joined to the institution and municipality dimensions.

select
    id
from {{ ref('cur_pix_key') }}
where id is null
    or key_type is null
    or key_value is null
    or person_type is null
    or ispb is null
    or length(ispb) <> 8
    or municipio_ibge is null
    or status is null
