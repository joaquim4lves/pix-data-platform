{# Drop keys whose latest CDC image is a delete.

   Called from the cur_* post-hook. The hook runs after delete+insert, so a
   key that disappeared from the select (because the winning op is delete)
   is removed here. An older delete that loses the lsn_ord ordering never
   becomes the intermediate row, and this statement does not touch the key.
#}
{% macro cdc_drop_deletes(intermediate_model) %}
    delete from {{ this }}
    where id in (
        select id
        from {{ ref(intermediate_model) }}
        where op = 'delete'
    )
{% endmacro %}
