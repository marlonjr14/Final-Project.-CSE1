import requests
import json

BASE_URL = 'http://localhost:5000/api'  # matches /api/pokemon routes

def test_get_all_pokemon():
    response = requests.get(f'{BASE_URL}/pokemon')
    print(f"GET /pokemon: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_get_pokemon_by_id(pokemon_id):
    response = requests.get(f'{BASE_URL}/pokemon/{pokemon_id}')
    print(f"GET /pokemon/{pokemon_id}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_create_pokemon(token):
    new_pokemon = {
        "name": "Testmon",
        "base_experience": 10,
        "height": 0.50,
        "weight": 5.00
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(f'{BASE_URL}/pokemon', json=new_pokemon, headers=headers)
    print(f"POST /pokemon: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)

def test_update_pokemon(pokemon_id, token):
    update_data = {
        "name": "UpdatedTestmon",
        "base_experience": 20,
        "height": 0.60,
        "weight": 6.00
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.put(f'{BASE_URL}/pokemon/{pokemon_id}', json=update_data, headers=headers)
    print(f"PUT /pokemon/{pokemon_id}: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)

def test_delete_pokemon(pokemon_id, token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.delete(f'{BASE_URL}/pokemon/{pokemon_id}', headers=headers)
    print(f"DELETE /pokemon/{pokemon_id}: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)

def test_xml_response():
    headers = {'Accept': 'application/xml'}
    response = requests.get(f'{BASE_URL}/pokemon', headers=headers)
    print(f"GET /pokemon (XML): {response.status_code}")
    print(response.text)

def get_token(username, password):
    resp = requests.post(f'{BASE_URL}/login', json={
        "username": username,
        "password": password
    })
    print(f"POST /login: {resp.status_code}")
    data = resp.json()
    return data.get("token")

if __name__ == '__main__':
    print("Testing Pokémon REST API\n")

    # First, make sure you have a user created via /api/register, then:
    token = get_token("your_username", "your_password")

    test_get_all_pokemon()
    print("\n" + "=" * 50 + "\n")
    test_get_pokemon_by_id(1)
    print("\n" + "=" * 50 + "\n")
    test_xml_response()

    if token:
        print("\n" + "=" * 50 + "\n")
        test_create_pokemon(token)
