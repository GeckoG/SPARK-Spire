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
cursorObject.execute("CREATE DATABASE spark_spire")

print("Database 'spark-spire' Created")
import mysql.connector
from mysql.connector import Error

try:
    # Attempt to connect to the MySQL database
    dataBase = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        passwd = 'Eequalsmc^2',
    )
    
    # If connection is successful
    if dataBase.is_connected():
        print("Successfully connected to the database")
        
        # Prepare a cursor object
        cursorObject = dataBase.cursor()
        
        # Create a new database
        cursorObject.execute("CREATE DATABASE spark_spire")
        print("Database 'spark_spire' created successfully.")
        
    # Commit the changes
    dataBase.commit()

except Error as e:
    # Print an error message if an exception occurs
    print("Error while connecting to MySQL or creating the database:", e)

finally:
    # Ensure that the database connection is closed
    if dataBase.is_connected():
        cursorObject.close()
        dataBase.close()
        print("MySQL connection is closed")
