-- One current row per dispute.

select
    id,
    count(*) as rows
from marts.cur_pix_dispute
group by id
having count(*) > 1
