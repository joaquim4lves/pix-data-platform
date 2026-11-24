-- One current row per PIX key.

select
    id,
    count(*) as rows
from marts.cur_pix_key
group by id
having count(*) > 1
