-- Bronze: monthly full extract from the source master system, kept for every extract date
-- so slowly-changing history can be rebuilt deterministically at any time.
select * exclude (filename), filename as _source_file
from read_csv('{{ var("landing") }}/store_ref/*/*.csv',
              header = true, all_varchar = true, union_by_name = true, filename = true)
