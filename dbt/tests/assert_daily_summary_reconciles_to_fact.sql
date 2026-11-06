-- The daily summary is a different shape of the same truth: totals must equal the fact (incl. restated lines).
select d.rev, f.rev, d.units, f.units
from (select sum(net_revenue) rev, sum(net_units) units from {{ ref('agg_sales_daily') }}) d,
     (select sum(net_sales_inr) rev, sum(qty) units from {{ ref('fct_sales_line') }}) f
where d.rev <> f.rev or d.units <> f.units
