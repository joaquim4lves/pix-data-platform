select
    r.ano_mes,
    r.valor_aceito,
    r.spi_valor,
    r.ratio_aceito_sobre_spi,
    r.caption
from {{ ref('fct_pix_med_vs_spi') }} as r
left join (
    select ano_mes, sum(valor) as spi_valor
    from {{ ref('fct_pix_transactions') }}
    group by ano_mes
) as spi
    on r.ano_mes = spi.ano_mes
where r.ano_mes < 202201
    or r.spi_valor is null
    or r.spi_valor = 0
    or abs(r.spi_valor - spi.spi_valor) > 0.000001
    or abs(r.ratio_aceito_sobre_spi - (r.valor_aceito / r.spi_valor)) > 0.000001
    or r.caption <> 'Approximate ratio computed by this portfolio; denominator is SPI-only (no on-us). Not an official BCB rate.'
    or r.ano_mes in (
        select ano_mes
        from {{ ref('fct_pix_med') }} as med
        where abs((r.ratio_aceito_sobre_spi * 100) - med.percentual_devolucao) < 0.000001
    )
