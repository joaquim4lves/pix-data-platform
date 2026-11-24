select
    ano_mes,
    natureza,
    valor,
    quantidade
from marts.fct_transacoes_mensal
where valor < 0
    or quantidade < 0
