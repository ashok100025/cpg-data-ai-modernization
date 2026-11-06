-- BOOK_IN_CURRENT must never move value out of the sale month: every line released with that decision is
-- booked in a later month than its sale (an adjustment line for corrections, the full line for new late lines).
select f.sales_line_key, f.event_date_local, f.accounting_month
from {{ ref('fct_sales_line') }} f
join {{ ref('slv_restatement_approvals') }} a on f.restatement_id = a.restatement_id
where a.decision = 'BOOK_IN_CURRENT' and f.accounting_month <= strftime(f.event_date_local, '%Y-%m')
