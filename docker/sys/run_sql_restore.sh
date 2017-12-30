#!/bin/bash
# Sleep before running report

docker start cont_db
sleep 60
docker exec cont_db /db_backup/restore_database.sh
