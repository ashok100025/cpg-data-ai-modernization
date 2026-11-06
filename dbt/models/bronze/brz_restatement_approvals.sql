-- Bronze: Finance restatement approvals as landed (append-only; header-only until the first approval).
select * exclude (filename), filename as _source_file
from {{ source('landing', 'restatements') }}
