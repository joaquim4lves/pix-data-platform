select forma_iniciacao_raw, forma_iniciacao_label
from {{ ref('fct_pix_transactions') }}
where (
        forma_iniciacao_raw = 'Nao disponivel'
        and forma_iniciacao_label <> 'Unstated / other (Nao disponivel)'
    )
    or (
        forma_iniciacao_raw in ('AUTO', 'APDN', 'APES')
        and forma_iniciacao_label <> forma_iniciacao_raw
    )
    or (
        forma_iniciacao_raw = 'DICT'
        and forma_iniciacao_label <> 'DICT · Pix key'
    )
    or (
        forma_iniciacao_raw = 'QRDN'
        and forma_iniciacao_label <> 'QRDN · dynamic QR'
    )
