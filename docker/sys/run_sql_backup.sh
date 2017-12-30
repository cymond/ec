#!/bin/bash
# Sleep before running report

#docker start cont_db
sleep 60
echo "Trying to exec backup_database script"
docker exec -it cont_db /db_backup/backup_database.sh
