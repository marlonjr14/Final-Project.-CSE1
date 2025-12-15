# Pokémon REST API with JWT Authentication

A REST API built with Flask and MySQL for managing Pokémon data. The API supports JWT-based authentication, search by name, and can return both JSON and XML responses. A simple web interface is included for listing and creating Pokémon

---

## Features

- **CRUD Operations** – Create, Read, Update, and Delete Pokémon via `/api/pokemon` endpoints.
- **Search** – Search Pokémon by name using query parameters.
- **Multiple Formats** – JSON by default.
- **MySQL Persistence** – Data stored in a MySQL database.
- **Web Interface** – HTML pages for viewing and adding Pokémon.

---

## 1. Prerequisites

Before running this project, install:

- Python **3.8+**
- MySQL Server (e.g., XAMPP / WAMP / standalone)
- `pip` (Python package manager)

---

## 2. Clone the Repository
https://github.com/marlonjr14/Final-Project.-CSE1.git

## 3. Set Up the MySQL Database

1. Start MySQL Server.
2. Create the database used by `app.py`:
3. Create the `pokemon` table and insert sample data (or import from your SQL file). Example schema matching the code:
USE pokemon_db;

CREATE TABLE pokemon (
id INT NOT NULL AUTO_INCREMENT,
name VARCHAR(50) NOT NULL,
base_experience INT,
height DECIMAL(4,2),
weight DECIMAL(5,2),
PRIMARY KEY (id)
);

4. (Automatically handled) – When you hit `/api/register`, the app will create a `users` table inside `pokemon_db` if it does not exist.

## 4. Create and Activate a Virtual Environment

From the project root:
python -m venv venv
venv\Scripts\activate

## 5. Install Dependencies
Inside the activated virtual environment, install required packages:
Flask
mysql-connector-python
dicttoxml
PyJWT
python-dotenv

## 6. Configure Environment Variables
Create a `.env` file in the project root:

This `SECRET_KEY` is used to sign JWT tokens. Never commit real secrets in public repos.
The database connection in `app.py`

## 7. Project Structure
A minimal structure for this project:
Final-Project.-CSE1/
├── app.py
├── Pokemon.xml # sample XML data
├── requirements.txt
├── .env
└── templates/
├── index.html # home page
├── pokemon.html # list/search Pokémon
└── create_pokemon.html # create Pokémon form

## 8. Running the Application

With MySQL running and the virtual environment activated:
python app.py

You should see: Running on http://127.0.0.1:5000

### 9. Public Pokémon endpoints

- `GET /api/pokemon` – Get all Pokémon.
- `GET /api/pokemon/<id>` – Get Pokémon by ID.
- `GET /api/pokemon/search?name=<name>` – Search Pokémon by name (partial match).

Example:
GET http://localhost:5000/api/pokemon

To receive XML:
GET http://localhost:5000/api/pokemon


The `format_response` helper reads the `Accept` header and uses `dicttoxml` when XML is requested. 

### 10. Protected Pokémon endpoints (JWT required)

These require `Authorization: Bearer <token>`:

- `POST /api/pokemon` – Create new Pokémon.
- `PUT /api/pokemon/<id>` – Update Pokémon.
- `DELETE /api/pokemon/<id>` – Delete Pokémon.

Example create request:

POST /api/pokemon
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
"name": "ScriptMon",
"base_experience": 80,
"height": 0.80,
"weight": 12.30
}

## 11. Error Handling

The app uses custom error handlers:

- `404` → `{"error": "Endpoint not found"}` (or XML equivalent).
- `500` → `{"error": "Internal server error"}`.

Common reasons for `Endpoint not found`:

- Typo in URL (e.g., `/api/pokemons` instead of `/api/pokemon`).
- Wrong HTTP method (e.g., using GET on a POST-only endpoint).

---

## 12. Stopping the App

- Press `Ctrl + C` in the terminal running `python app.py`.
- Deactivate the virtual environment with: deactivate

------

This README documents how to clone, install, configure, and run your Pokémon REST API project, and how to use both the web interface and the JWT-secured REST endpoints.