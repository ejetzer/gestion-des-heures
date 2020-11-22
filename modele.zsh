cd {repertoire}
export table={table}
export temps={temps}
export desc={desc}
export atelier={atelier}
export colonnes={colonnes}
envsubst < {requete} > script.sql
mysql < script.sql > script.out
cat script.out
unset table
unset temps
unset desc
unset atelier
rm script.sql
exit