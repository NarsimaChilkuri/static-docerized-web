from flask import Flask, render_template, request, redirect
from flaskext.mysql import MySQL
import json
import string
import random
import docker
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'ci_cd'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql = MySQL()
mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor()
port = 5001
@app.route("/github-data",methods=['GET','POST'])
def create_table():
    global port
    if request.headers['Content-Type'] == 'application/json':
       response_str = json.dumps(request.json)
       response_json = json.loads(response_str)
       commit_id = response_json["commits"][0]["id"]
       user_name = response_json["commits"][0]["committer"]["username"]
       user_email = response_json["commits"][0]["committer"]["email"]
       branch = response_json["ref"]
       files_added = response_json["commits"][0]["added"]
       files_removed = response_json["commits"][0]["removed"]
       files_modified = response_json["commits"][0]["modified"]
       commit_message = response_json["commits"][0]["message"]
       timestamp = response_json["commits"][0]["timestamp"]
       image_tag = "74744556/static-web-page:{}".format(commit_id)
       client = docker.from_env()
       client.images.build(path="/home/narsimac/static-web-container/",tag=image_tag)
       client.images.push("74744556/static-web-page",commit_id)
       print commit_id
       print user_name
       print user_email
       print branch
       print files_added
       print files_removed
       print files_modified
       print commit_message
       print timestamp
       
       domain=domain_generator()
       cursor.execute("select count(*) from git_log")
       rowcount = cursor.fetchone()[0] + 1
      

       query = "INSERT INTO git_log (user_email, user_name, branch_name, commit_hash, domain_name,port,files_added,files_modified,files_removed,commit_message,timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
       values = (user_email,user_name,branch,commit_id,domain,port,listToString(files_added),listToString(files_modified),listToString(files_removed),commit_message,timestamp)
       cursor.execute(query,values)
       port += 1
       if rowcount > 3:
          delete_query = "DELETE FROM git_log LIMIT 1"
          cursor.execute(delete_query)
          update_query = "UPDATE git_log SET id = id - 1"
          cursor.execute(update_query)
          update_query_port = "UPDATE git_log SET port = port - 1"
          cursor.execute(update_query_port)
       conn.commit()
       cursor.execute("select domain_name from git_log")
       hosts = cursor.fetchall()
       f = open('/etc/hosts', 'w')
       f.write("127.0.0.1        localhost\n")
       f.write("127.0.1.1        TGN1052\n")
       for row in hosts:
           f.write("127.0.0.1        %s\n" % row)
       f.close()
       port_query = "SELECT port FROM git_log"
       cursor.execute(port_query)
       ports_list = list(cursor.fetchall())
       container = client.containers.run(image_tag, detach=True,ports={'80/tcp': ports_list})
       print container.logs()
       return "Successfully Done"

def listToString(s):  
    str1 = " "   
    return (str1.join(s)) 

def domain_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
  
if __name__ == "__main__":
    app.run(debug=True)
