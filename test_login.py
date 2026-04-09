import requests
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

register_resp = requests.post('http://127.0.0.1:5000/register', json={
    'name': 'test',
    'email': 'test@test.com',
    'password': '123456',
    'car_number': '12a 3456'
})
print('Register:', register_resp.status_code)

login_resp = requests.post('http://127.0.0.1:5000/login', json={
    'email': 'test@test.com',
    'password': '123456'
})
print('Login:', login_resp.status_code, login_resp.json())