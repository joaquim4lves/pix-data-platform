-- One current row per operational transaction.

select
    id,
    count(*) as rows
from marts.cur_pix_transaction
group by id
having count(*) > 1
