import string
import time
import cx_Oracle
   
  #set variables
OraUid="hr"        #Oracle User  
OraPwd="hr"       #Oracle password
OraService="PDBSAM"    #Oracle Service name From Tnsnames.ora file
   
  #get the current date

TIME_N = time.strftime("%d%m", time.localtime(time.time()))
now = TIME_N.upper()   
db = cx_Oracle.connect(OraUid + "/" + OraPwd + "@" + OraService)    #Connect to database
c = db.cursor()                                                     #Allocate a cursor
c.execute("select first_name from employees where employee_id = 100")                       #Execute a SQL statement
print ("Records selected python-> Oracle:")
#print (c.fetchall())  #Print all results
name = c.fetchall()
print ("Name is: ", name[0][0])
c.close()           #Close the database connection