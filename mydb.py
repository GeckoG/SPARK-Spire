# Install Mysql on your computer
# pip install mysql
# pip install mysql-connector
# pip install mysql-connector-python

import mysql.connector

dataBase = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    passwd = 'Eequalsmc^2'

    )

# prepare a cursor object
cursorObject = dataBase.cursor()

# Create db
cursorObject.execute("CREATE DATABASE backtrackstats")

print("Database 'backtrackstats' Created")