-- One current row per dispute.

select
    id,
    count(*) as rows
from {{ ref('cur_pix_dispute') }}
group by id
having count(*) > 1
