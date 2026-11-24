-- One row per AnoMes present in any raw entity.
-- The series is monthly. data_inicio is the first day and data_fim is the
-- last day, including 29 February in a leap year. There is no day grain.
-- Grain: ano_mes (YYYYMM).

with months as (
    select ano_mes
    from {{ ref('int_transacoes_mensal') }}
    union
    select ano_mes
    from {{ ref('int_transacoes_municipio') }}
    union
    select ano_mes
    from {{ ref('int_chaves_pix') }}
),
parts as (
    select
        ano_mes,
        cast(substr(lpad(cast(ano_mes as varchar), 6, '0'), 1, 4) as integer) as ano,
        cast(substr(lpad(cast(ano_mes as varchar), 6, '0'), 5, 2) as integer) as mes
    from months
)
select
    ano_mes,
    ano,
    mes,
    cast(floor((mes - 1) / 3) as integer) + 1 as trimestre,
    cast(
        concat(cast(ano as varchar), '-', lpad(cast(mes as varchar), 2, '0'), '-01') as date
    ) as data_inicio,
    cast(
        concat(
            cast(ano as varchar),
            '-',
            lpad(cast(mes as varchar), 2, '0'),
            '-',
            case
                when mes in (1, 3, 5, 7, 8, 10, 12) then '31'
                when mes in (4, 6, 9, 11) then '30'
                when mes = 2 and (
                    ano % 400 = 0 or (ano % 4 = 0 and ano % 100 <> 0)
                ) then '29'
                else '28'
            end
        ) as date
    ) as data_fim,
    case mes
        when 1 then 'Janeiro'
        when 2 then 'Fevereiro'
        when 3 then 'Março'
        when 4 then 'Abril'
        when 5 then 'Maio'
        when 6 then 'Junho'
        when 7 then 'Julho'
        when 8 then 'Agosto'
        when 9 then 'Setembro'
        when 10 then 'Outubro'
        when 11 then 'Novembro'
        when 12 then 'Dezembro'
    end as nome_mes,
    concat(cast(ano as varchar), '-', lpad(cast(mes as varchar), 2, '0')) as rotulo
from parts
