#######################IMPORTANT##########################

# THIS IS JUST A TEMPLATE
# It won't work completely by taking this template, this
#   is meant to help you get start if you choose to
#   store your photos using BLOB.
# I tried my best to provide you with example code that
#   reflects the finstagram schema we are using.

# For further information refer to this link
# https://pynative.com/python-mysql-blob-insert-retrieve-file-image-as-a-blob-in-mysql/

#######################IMPORTANT##########################

import mysql.connector
from mysql.connector import Error

#####################################################
# Inserting Images as BLOB data into MySQL Table
#####################################################

connection = mysql.connector.connect(host='127.0.0.1',
                                     database='Finstagram',
                                     port = 8889,
                                     user='root',
                                     password='root')
        
def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def insertBLOB(username, photo, allFollowers, caption):
    print("Inserting BLOB into photo table")

    #username = request.form['username']
    #postingDate = request.form['postingDate']
    #allFollowers = request.form['allFollowers']
    #caption = request.form['caption']

    #   Just to clarify since you specify that the table auto increments photoIDs
    #   You do not havy to insert into that column since that will be done for you.

    try:
        cursor = connection.cursor()
        sql_insert_blob_query = 'INSERT INTO Photo(filePath, allFollowers, caption, poster) VALUES (%s,%s,%s,%s)'

        photo = convertToBinaryData(photo)

        # Convert data into tuple format
        insert_blob_tuple = (photo, allFollowers, caption, username)
        result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
        connection.commit()
        print("Image and file inserted successfully as a BLOB into Photos table", result)
        #if (allFollowers == '0'): 
            #print("hello") 
            #query = 'INSERT INTO SharedWith (pID, groupName, groupCreator) VALUES(LAST_INSERT_ID(), %s, %s)'
            
        cursor.execute('SELECT LAST_INSERT_ID() AS pID')
        data = cursor.fetchall()
        for row in data:
            pID=row[0]
            print(row[0])
            #connection.commit()

    except mysql.connector.Error as error:
        print("Failed inserting BLOB data into MySQL table {}".format(error))

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
            return pID

################################################################
# Retrieving Image and File stored as a BLOB from MySQL Table
################################################################

def write_file(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)

def readBLOB(photoId, photo):
    print("Reading BLOB data from Photo table")

    try:
        cursor = connection.cursor()
        sql_fetch_blob_query = 'SELECT filePath FROM Photo WHERE pID = %s'

        cursor.execute(sql_fetch_blob_query, (photoId,))
        record = cursor.fetchall()
        for row in record:
            #print("photoID = ", row[0], )
            image = row[0]
            print("Storing photo on disk \n")
            write_file(image, photo)

    except mysql.connector.Error as error:
        print("Failed to read BLOB data from MySQL table {}".format(error))

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

#insertBLOB("Kevin", "Path_to_image\images\photo1.png")

#readBLOB(photoId, "Path_to_image\my_SQL\query_output\photo1.png")
