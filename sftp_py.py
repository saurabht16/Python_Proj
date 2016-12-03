from __future__ import print_function

## Copy files unattended over SSH using a glob pattern.
## It tries first to connect using a private key from a private key file
## or provided by an SSH agent. If RSA authentication fails, then 
## password login is attempted.

##
## DEPENDENT MODULES:
##      * paramiko, install it with `easy_install paramiko`

## NOTE: 1. The script assumes that the files on the source
##       computer are *always* newer that on the target;
##       2. no timestamps or file size comparisons are made
##       3. use at your own risk

password = 'redhat'
rsa_private_key = r'C:\Users\Saurabh\Documents\Python_docs\python.pem'
    
import os
import glob
import paramiko
import hashlib
import base64
import sys
import string
import time
import cx_Oracle

def agent_auth(transport, username):
    """
    Attempt to authenticate to the given transport using any of the private
    keys available from an SSH agent or from a local private RSA key file (assumes no pass phrase).
    """
    try:
        ki = paramiko.RSAKey.from_private_key_file(rsa_private_key)
    except Exception as e:
          print ('Failed loading' % (rsa_private_key, e))

    agent = paramiko.Agent()
    agent_keys = agent.get_keys() + (ki,)
    if len(agent_keys) == 0:
        return

    for key in agent_keys:
        My_Key = key.get_fingerprint()
        print ('Trying ssh-agent key %s' % key.get_fingerprint()),
        try:
            transport.auth_publickey(username, key)
            print ('... success!')
            return

        except paramiko.SSHException:
            print ('... failed! SSH')

def sftp_file(type):
    OraUid="hr"        #Oracle User  
    OraPwd="hr"       #Oracle password
    OraService="PDBSAM"    #Oracle Service name From Tnsnames.ora file
    TIME_N = time.strftime("%d%m", time.localtime(time.time()))
    now = TIME_N.upper()   
    db = cx_Oracle.connect(OraUid + "/" + OraPwd + "@" + OraService)    #Connect to database
    c = db.cursor()   
    sql = "select s.REMOTE_HOST, s.PORT, s.LOCAL_DIR, s.REMOTE_DIR, s.remote_user ,f.file_pattern from sftp_frame s, sftp_file f where  s.sftp_type = :stype"                                                  #Allocate a cursor
    c.execute(sql, stype=type)                       #Execute a SQL statement
    print ("Records selected python-> Oracle:")
    data = c.fetchall()
     # remote hostname where SSH server is running
    #print (c.fetchall())  #Print all results
    if len(list(data)) : 
        hostname = data[0][0]
        port = data[0][1]
        username = data[0][4]
        dir_local = data[0][2]
        dir_remote = data[0][3]
        file_pattern = []
        for dt in data:
            file_pattern.append(dt[5]) 
        print (hostname)
        print (port)
        print (username)
        print (dir_local)
        print (dir_remote)
        print (file_pattern)
        return hostname, port, username, dir_local, dir_remote, file_pattern
    else :
        print ("Query Retured No Results. Please check The SFTP Type Passed")
        c.close()
        sys.exit(1)
    
    c.close()           #Close the database connection
    #os.path.expanduser('~/.ssh/id_rsa')
    #dir_local=r'C:\Users\Saurabh\Documents\Python_docs'
    #dir_remote = "/home/saurabh/sam"
 
  #get the current date

    


# get host key, if we know one
hostkeytype = None
hostkey = None
files_copied = 0
try:
    host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
except IOError:
    try:
        # try ~/ssh/ too, e.g. on windows
        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
    except IOError as e:
        print ('*** Unable to open host keys file%s: %s' % (e.__class__, e))
        host_keys = {}

stype = sys.argv[1]
try:
    hostname, port, username, dir_local, dir_remote, file_pattern = sftp_file(stype)
except cx_Oracle.DatabaseError as e:
    print("Please enter a Valid Value")
    sys.exit(1)
if hostname in host_keys:
    hostkeytype = host_keys[hostname].keys()[0]
    hostkey = host_keys[hostname][hostkeytype]
    print ('Using host key of type %s' % hostkeytype)

# now, connect and use paramiko Transport to negotiate SSH2 across the connection
try:
    print ('Establishing SSH connection to:', hostname, port, '...')
    t = paramiko.Transport((hostname, port))
    t.start_client()
    agent_auth(t, username)
    if not t.is_authenticated():
        print ('RSA key auth failed! Trying password login...')
        t.auth_password(username=username, password=password)
    else:
        sftp = t.open_session()
    sftp = paramiko.SFTPClient.from_transport(t)

    # dirlist on remote host
#    dirlist = sftp.listdir('.')
#    print "Dirlist:", dirlist

    try:
        sftp.mkdir(dir_remote)
    except IOError as e:
        print ('(assuming ', dir_remote, 'exists)', e)

#    print 'created ' + dir_remote +' on the hostname'

    # BETTER: use the get() and put() methods
    # for fname in os.listdir(dir_local):
    for file_pat in file_pattern:
        for fname in glob.glob(dir_local + os.sep + file_pat):
            is_up_to_date = False
            if fname.lower().endswith(''):
                local_file = os.path.join(dir_local, fname)
                remote_file = dir_remote + '/' + os.path.basename(fname)
            #if remote file exists
                try:
                    if sftp.stat(remote_file):
                    
                        local_file_data = open(local_file, "rb").read()
                        remote_file_data = sftp.open(remote_file).read()
                        md1 = hashlib.md5(remote_file_data).hexdigest()
                        md2 = hashlib.md5(local_file_data).hexdigest()
                        if md1 == md2:
                            is_up_to_date = True
                            print ("UNCHANGED:", os.path.basename(fname))
                        else:
                            print ("MODIFIED:", os.path.basename(fname)),
                except Exception as e:
                    #print ('*** Caught exception: %s: %s' % (e.__class__, e))
                    print ("NEW: ", os.path.basename(fname)),

                if not is_up_to_date:
                    print ('Copying', local_file, 'to ', remote_file)
                    sftp.put(local_file, remote_file)
                    files_copied += 1
    t.close()

except Exception as e:
    print ('*** Caught exception: %s: %s' % (e.__class__, e))
    try:
        t.close()
    except:
        pass
print ('=' * 60)
print ('Total files copied:',files_copied)
print ('All operations complete!')
print ('=' * 60)
