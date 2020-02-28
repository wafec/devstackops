#!/bin/sh
rm tests.db
sqlite3 tests.db <<EOF
.read sql/01-first-tables.sql
.read sql/02-injection-tables.sql
.read sql/03-control-tables.sql
insert into experiment (exp_id, exp_target) values (1, 'test');
EOF