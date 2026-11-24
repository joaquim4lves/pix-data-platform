-- One current row per PIX key.

select
    id,
    count(*) as rows
from {{ ref('cur_pix_key') }}
group by id
having count(*) > 1
