-- Operational keys joined to the BCB municipality dimension.
-- Keys whose municipio_ibge is not in the extract (or is 0, Não informado,
-- only when that member was built) do not appear. This is a count of the
-- simulated registry, not the national key stock in fct_chaves_pix.

select
    municipio.nome,
    municipio.uf_sigla,
    count(*) as keys
from marts.cur_pix_key as pix_key
join marts.dim_municipio as municipio
    on pix_key.municipio_ibge = municipio.municipio_ibge
group by
    municipio.nome,
    municipio.uf_sigla
order by
    keys desc,
    municipio.nome
