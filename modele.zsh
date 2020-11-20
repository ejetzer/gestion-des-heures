cd {répertoire}
export table={table}
export temps={temps}
export desc={desc}
export atelier={atelier}
mysql < envsubst < {requête} > mysql.out
cat mysql.out
exit