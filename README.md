# Django Real-Time Robot Connection System

This Django-based project is a server-side application that facilitates secure real-time communication between users and their robots. The system ensures secure connections using SSL certificates and manages these interactions through asynchronous WebSockets. Additionally, the server manages user accounts, ensuring that each user is linked to their respective robot, with user-robot pairs stored and managed in a database.

## Features

- **Real-time Communication**: The system supports asynchronous WebSocket communication to provide real-time interaction between users and their robots.
- **Secure Communication**: The system employs SSL certificates to ensure secure communications between the server and the robots.
- **User Authentication and Management**: Users can create accounts, log in, and are linked to their corresponding robots.
- **WebSocket Handling**: The system matches WebSocket connections between users and their assigned robots.
- **Nginx Integration**: The application is integrated with Nginx to handle SSL termination and improve performance.

## Prerequisites

- Python 3.x
- Django 3.x+
- Channels (for WebSocket handling)
- PostgreSQL (or other supported databases)
- Redis (for Channels layer support)
- Nginx
- SSL Certificate (for secure robot-server communication)

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Hayan47/Maestro-Server.git
    cd Maestro-Server
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Setup the database**:
    - Configure your database settings in `settings.py`:
      ```python
      DATABASES = {
          'default': {
              'ENGINE': 'django.db.backends.postgresql',
              'NAME': '<your_db_name>',
              'USER': '<your_db_user>',
              'PASSWORD': '<your_db_password>',
              'HOST': 'localhost',
              'PORT': '5432',
          }
      }
      ```
    - Apply the migrations:
      ```bash
      python manage.py migrate
      ```

5. **Configure Redis for Channels**:
    - Ensure Redis is running locally or on a configured server.
    - Update Channels settings in `settings.py`:
      ```python
      CHANNEL_LAYERS = {
          'default': {
              'BACKEND': 'channels_redis.core.RedisChannelLayer',
              'CONFIG': {
                  "hosts": [('127.0.0.1', 6379)],
              },
          },
      }
      ```

6. **Generate SSL Certificates with OpenSSL**:
    You can generate your own CA certificate, server certificate, and key using OpenSSL:
    - **Generate a CA certificate**:
      ```bash
      openssl req -new -x509 -days 365 -keyout ca-key.pem -out ca-cert.pem
      ```
    - **Generate a server private key**:
      ```bash
      openssl genrsa -out server-key.pem 2048
      ```
    - **Generate a Certificate Signing Request (CSR)**:
      ```bash
      openssl req -new -key server-key.pem -out server.csr
      ```
    - **Sign the server certificate using the CA**:
      ```bash
      openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem -days 365
      ```

    Once generated, move the SSL certificates and key to the Nginx folder (for example, `C:\nginx\ssl`):
    - `server-cert.pem`
    - `server-key.pem`

7. **Configure Nginx**:
    - Add an Nginx configuration for SSL and WebSocket proxying:
      ```nginx
      server {
          listen 443 ssl;
          server_name yourdomain.com;

          ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
          ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

          location / {
              proxy_pass http://127.0.0.1:8000;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Proto $scheme;
          }

          location /ws/ {
              proxy_pass http://127.0.0.1:8000;
              proxy_http_version 1.1;
              proxy_set_header Upgrade $http_upgrade;
              proxy_set_header Connection "upgrade";
              proxy_set_header Host $host;
          }
      }
      ```

8. **Run the server**:
    ```bash
    python manage.py runserver
    ```

9. **Start Redis server**:
    Ensure Redis is running:
    ```bash
    redis-server
    ```

## Usage

- **User Account Management**: Users can sign up and log in to the platform.
- **Robot Pairing**: Each user is assigned a robot in the database. The system manages and matches the real-time connections between users and their respective robots using WebSocket communication.
- **SSL Security**: Robots communicate with the server over a secure SSL-encrypted connection.

## Structure

- `models.py`: Contains the `User` and `Robot` models, where each `Robot` is linked to a `User`.
- `consumers.py`: Defines WebSocket consumers for managing real-time communication between users and robots.
- `urls.py`: Defines the API and WebSocket endpoints.
- `settings.py`: Configuration for database, Channels, SSL, and more.
- `nginx.conf`: Sample Nginx configuration for proxying and SSL setup.
