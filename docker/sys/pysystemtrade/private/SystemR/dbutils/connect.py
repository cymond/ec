from playhouse.csv_loader  import *
import peewee as pw
from peewee import *

def opendb(username, password, database, port=3306, host="0.0.0.0"):

    db = pw.MySQLDatabase(port=port, host=host, user=username, passwd=password, database=database)
    return db

def dtab_from_qundl_csv(database, csv_file):
    table = load_csv(database, csv_file)
    print(csv_file)
    return table

'''
class MySQLModel(pw.Model):
    class Meta:
        database = db

class test_user(MySQLModel):
    ID = pw.IntegerField(primary_key=True)
    user_name = pw.CharField()
    user_email = pw.CharField()

class Table(Model):
    username = CharField()
    join_date = DateTimeField()
    about_me = TextField()

db.connect()

matching_users = test_user.select()
print(matching_users[0].ID, matching_users[0].user_name, matching_users[0].user_email)
print("-----------------")
print(matching_users[0])
'''