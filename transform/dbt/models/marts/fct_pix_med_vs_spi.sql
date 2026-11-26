-- National ratio of MED accepted contested value to SPI settled value
-- for the same AnoMes. The two facts have different grains: MED is one
-- national row, SPI is the transaction cube. The denominator is the sum
-- of fct_pix_transactions.valor, which is SPI-only. Months without a MED
-- row are not filled with zero. This is not PercentualdeDevolucao.

select
    med.ano_mes,
    med.month_start,
    med.is_complete_month,
    med.valor_aceito,
    spi.spi_valor,
    med.valor_aceito / nullif(spi.spi_valor, 0) as ratio_aceito_sobre_spi,
    'Approximate ratio computed by this portfolio; denominator is SPI-only (no on-us). Not an official BCB rate.'
        as caption
from {{ ref('fct_pix_med') }} as med
inner join (
    select ano_mes, sum(valor) as spi_valor
    from {{ ref('fct_pix_transactions') }}
    group by ano_mes
) as spi
    on med.ano_mes = spi.ano_mes
where med.ano_mes >= 202201
    and spi.spi_valor is not null
    and spi.spi_valor <> 0
