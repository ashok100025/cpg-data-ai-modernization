select * exclude (filename), filename as _source_file
from read_csv('{{ var("landing") }}/promotions/*.csv',
              header = true, all_varchar = true, filename = true)
