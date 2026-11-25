select
    'Age is national only. Clear the state and municipality filters. This series has no municipality grain.' as notice
from (select 1) as _
where {{state}} <> 'All' or {{municipality}} <> ''
