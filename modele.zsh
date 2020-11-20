cd {répertoire}
export table={table}
export temps={temps}
export desc={desc}
export atelier={atelier}
envsubst < {requête} > script.sql
mysql < script.sql > script.out
cat script.out
unset table
unset temps
unset desc
unset atelier
rm script.sql
exit