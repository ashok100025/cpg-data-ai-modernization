-- Bronze: monthly full extract from the source master system, kept for every extract date
-- so slowly-changing history can be rebuilt deterministically at any time.
select * exclude (filename), filename as _source_file
from {{ source('landing', 'pim_product') }}
