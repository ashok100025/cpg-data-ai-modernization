{# Generic test: the mart's grain columns identify exactly one row (written here to avoid a package dependency). #}
{% test unique_mart_grain(model) %}
select week, region, category, channel, count(*) as n
from {{ model }}
group by 1, 2, 3, 4
having count(*) > 1
{% endtest %}
