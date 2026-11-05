select * exclude (filename), filename as _source_file
from {{ source('landing', 'promotions') }}
