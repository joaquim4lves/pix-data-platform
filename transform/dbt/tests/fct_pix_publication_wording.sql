select banner, gap_note
from {{ ref('fct_pix_publication') }} as publication
where banner is distinct from (
        'MED figures are national, monthly, and published 30 days after month-end. Latest month in this extract: '
        || case
            when med_latest_complete is null then 'none'
            else {{ ano_mes_label('med_latest_complete') }}
        end
    )
    or gap_note is distinct from (
        case
            when transactions_latest_complete is not null
                and med_latest_complete is not null
                and med_latest_complete < transactions_latest_complete
                then {{ month_name('transactions_latest_complete') }}
                    || ' not published yet; last month is '
                    || {{ month_name('med_latest_complete') }}
                    || ' '
                    || substr(lpad(cast(med_latest_complete as varchar), 6, '0'), 1, 4)
            else null
        end
    )
