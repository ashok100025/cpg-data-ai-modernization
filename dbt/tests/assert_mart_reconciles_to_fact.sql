-- The mart is a different shape of the same truth: its totals must equal the fact's.
select m.rev as mart_revenue, f.rev as fact_revenue, m.units as mart_units, f.units as fact_units
from (select sum(net_revenue) rev, sum(net_units) units from {{ ref('mart_sales_weekly') }}) m,
     (select sum(net_sales_inr) rev, sum(qty) units from {{ ref('fct_sales_line') }}) f
where m.rev <> f.rev or m.units <> f.units
