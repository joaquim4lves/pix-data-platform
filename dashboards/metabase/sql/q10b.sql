with latest as (
    select *
    from marts.fct_pix_med
    where ano_mes = (select max(ano_mes) from marts.fct_pix_med where is_complete_month)
)
select 'Insufficient balance' as category, 'reason' as kind,
    case when {{med_measure}} = 'count' then quantidade_nao_devolvida_saldo else valor_nao_devolvido_saldo end as amount
from latest
union all
select 'Account closed', 'reason',
    case when {{med_measure}} = 'count' then quantidade_nao_devolvida_conta else valor_nao_devolvido_conta end
from latest
union all
select 'Other', 'reason',
    case when {{med_measure}} = 'count' then quantidade_nao_devolvida_outros else valor_nao_devolvido_outros end
from latest
union all
select 'Full return (comparison)', 'comparison',
    case when {{med_measure}} = 'count' then quantidade_devolvida_integral else valor_devolvido_integral end
from latest
union all
select 'Partial return (comparison)', 'comparison',
    case when {{med_measure}} = 'count' then quantidade_devolvida_parcial else valor_devolvido_parcial end
from latest
