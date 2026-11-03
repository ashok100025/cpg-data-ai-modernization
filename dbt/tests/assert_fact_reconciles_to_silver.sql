-- Gold must not gain or lose lines or units versus validated silver (no fan-out from joins).
select s.n as silver_rows, f.n as fact_rows, s.q as silver_qty, f.q as fact_qty
from (select count(*) n, sum(qty) q from {{ ref('slv_sales') }}) s,
     (select count(*) n, sum(qty) q from {{ ref('fct_sales_line') }}) f
where s.n <> f.n or s.q <> f.q
