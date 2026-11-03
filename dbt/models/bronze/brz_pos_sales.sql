-- Bronze: store POS lines exactly as landed. All columns read as text (schema-on-read) so a
-- type change in the source (e.g. QTY sent as '3.0') never breaks ingestion; typing happens in silver.
select
    * exclude (filename),
    regexp_extract(filename, 'batch=([0-9]{4}-[0-9]{2})', 1) as _batch,
    filename                                                 as _source_file
from read_csv('{{ var("landing") }}/pos/*/*.csv',
              header = true, all_varchar = true, union_by_name = true, filename = true)
