import requests

# Test health
r = requests.get('http://127.0.0.1:5000/health')
print('Health:', r.json())

# Test register
r = requests.post('http://127.0.0.1:5000/register', json={
    'name': '딘',
    'email': 'test@test.com',
    'password': '123456',
    'car_number': '12가 3456'
})
print('Register:', r.status_code, r.text)

# Test get users
r = requests.get('http://127.0.0.1:5000/users')
print('Users:', r.json())
