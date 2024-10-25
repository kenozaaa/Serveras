# serve.py
from waitress import serve
from maintenance_calculator.wsgi import application

if __name__ == '__main__':
    serve(application, host='0.0.0.0', port=88)
