-- Gold: calendar with the retail/fiscal calendar (assumption A-04): fiscal year starts on the
-- Monday of the week containing 1 April; quarters of 13 weeks split 4-4-5; week 53 folds into P12.
with d as (
    select cast(range as date) as date_day
    from range(date '2024-01-01', date '2028-01-01', interval 1 day)
),
fy as (
    select date_day,
        case when date_day >= date_trunc('week', make_date(year(date_day), 4, 1))
             then year(date_day) else year(date_day) - 1 end as fy_start_year
    from d
),
w as (
    select *,
        cast(date_trunc('week', make_date(fy_start_year, 4, 1)) as date) as fy_anchor,
        date_diff('day', cast(date_trunc('week', make_date(fy_start_year, 4, 1)) as date), date_day) // 7 + 1 as fiscal_week
    from fy
),
q as (
    select *, least((fiscal_week - 1) // 13, 3) + 1 as fiscal_quarter from w
)
select
    cast(strftime(date_day, '%Y%m%d') as integer)            as date_key,
    date_day,
    cast(date_trunc('week', date_day) as date)               as week_start,
    isodow(date_day)                                         as iso_day_of_week,
    dayname(date_day)                                        as day_name,
    cast(date_trunc('month', date_day) as date)              as month_start,
    year(date_day)                                           as calendar_year,
    'FY' || fy_start_year || '-' || right(cast(fy_start_year + 1 as varchar), 2) as fiscal_year,
    fiscal_quarter,
    fiscal_week,
    (fiscal_quarter - 1) * 3 +
      case when fiscal_week - (fiscal_quarter - 1) * 13 <= 4 then 1
           when fiscal_week - (fiscal_quarter - 1) * 13 <= 8 then 2 else 3 end as fiscal_period
from q
