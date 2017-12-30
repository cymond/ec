#!/bin/bash
# Run download process
# 1 Download data
# 2 Run system and store in pickle file
# 3 Use stored pickle to generate reports

res1=$(date +%s.%N)
cd /home/ubuntu/docker/sys/
sleep 30
docker start cont_db
docker-compose -f docker-compose.yml -f docker-compose-daily-update.yml run --rm app
if [ $? -eq 0 ] 
	then
	echo "*****************************************************************"	
	echo "Successfuly completed data downloads. Starting Generate Trades..."
	docker start cont_db
	docker-compose -f docker-compose.yml -f docker-compose-gen-trades.yml run --rm app
	if [ $? -eq 0 ]
		then
		echo "*****************************************************************"	
		echo "Successfuly completed Generate Trades. Starting Generate Reports ..."
		docker start cont_db
		docker-compose -f docker-compose.yml -f docker-compose-gen-report.yml run --rm app
		if [ $? -eq 0 ]
			then
			echo " "
			echo "*****************************************************************"
			echo "*** SUCCESS! ***	"
			echo "Successfuly Generate Reports ..."
			echo "*****************************************************************"
			echo " "
		else
			echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
			echo "Problem with Generate Reports !!!!! "
		fi
	
	else
		echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		echo "Problem with Generate Trades !!!! "
	fi
else
	echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	echo "Problem with Data Downloads !!!!! "
fi

# Record run's total execution time
res2=$(date +%s.%N)
dt=$(echo "$res2 - $res1" | bc)
dd=$(echo "$dt/86400" | bc)
dt2=$(echo "$dt-86400*$dd" | bc)
dh=$(echo "$dt2/3600" | bc)
dt3=$(echo "$dt2-3600*$dh" | bc)
dm=$(echo "$dt3/60" | bc)
ds=$(echo "$dt3-60*$dm" | bc)

echo "END ==========================================================================="
printf "Total runtime: %d:%02d:%02d:%02.4f\n" $dd $dh $dm $ds
echo "END ==========================================================================="
# Only shutdown if script has run for longer than 10 minutes
if (( dt > 600 )); then
    echo "Shutting down"
    sudo shutdown -h now
else
    echo "Something wrong! Shutdown aborted!"
fi
