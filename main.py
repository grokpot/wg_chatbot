import datetime
from flask import Flask

app = Flask('My little Python App') 

@app.route('/') 
def index(): 
    return 'Hy you! The time is: ' + str(datetime.datetime.now().time())

if __name__ == '__main__':
    app.run(host='0.0.0.0')
