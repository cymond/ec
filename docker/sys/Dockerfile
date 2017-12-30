FROM python:3.5.4
MAINTAINER Pete Kawuki

COPY pysystemtrade/ /pysystemtrade/
COPY ibpythonsetup/ /ibpythonsetup/

RUN pip3 install pandas==0.19.2
RUN pip3 install pyyaml
RUN pip3 install scipy
RUN pip3 install matplotlib
RUN pip3 install quandl
RUN pip3 install sqlalchemy
RUN pip3 install swigibpy
RUN pip3 install pymysql
WORKDIR /ibpythonsetup/IBJts/source/pythonclient
RUN python3 setup.py install
WORKDIR //pysystemtrade/private/SystemR


ENV PYTHONPATH /pysystemtrade:/pysystemtrade/systems:/pysystemtrade/private/SystemR:$PYTHONPATH

ADD run_daily_update.sh run_daily_update.sh
ADD run_data_backup.sh run_data_backup.sh
ADD run_data_restore.sh run_data_restore.sh
ADD run_gen_report.sh run_gen_report.sh
ADD run_gen_trades.sh run_gen_trades.sh
ADD run_rolls_update.sh run_rolls_update.sh
ADD run_test.sh run_test.sh

CMD ["python3", "/pysystemtrade/private/SystemR/dbutils/restore_database.py"] 

