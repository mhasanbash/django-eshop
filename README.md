<div align="center">

# 🛍️ Django E-Commerce Backend

### A RESTful E-Commerce API Built with Django REST Framework

A modular e-commerce backend featuring product and inventory management, OTP-based authentication, online payments, and real-time customer support chat.

<br>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-red?style=for-the-badge&logo=django&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--Time-blueviolet?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker_Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-4051B5?style=for-the-badge&logo=gunicorn&logoColor=white)

</div>

---

## 📌 Overview

This project is a modular e-commerce backend developed with **Django and Django REST Framework (DRF)**. It provides APIs for managing products, inventory, customer accounts, orders, and payments, alongside a real-time communication system for customer support.

The application is organized into three main Django apps:

- **Store:** Product and inventory management, order processing, and Zarinpal payment integration.
- **Accounts:** Custom user management, OTP-based phone number authentication, and discount code management.
- **Chat:** Real-time messaging between customers and support staff using Django Channels and WebSockets.

The project is designed to provide a structured backend foundation for an online store and its frontend applications.

## ✨ Features

### 🛒 Store & Order Management

- Product management through dedicated API endpoints.
- Inventory management and stock tracking.
- Shopping order registration and processing.
- Integration with the Zarinpal payment gateway.
- Product availability and pricing management.

### 🔐 Authentication & Account Management

- Custom Django user model based on `AbstractBaseUser`.
- Phone number as the primary authentication identifier.
- OTP-based authentication using SMS verification.
- JWT access and refresh token generation.
- OTP expiration and verification attempt tracking.
- Resend cooldown to reduce repeated OTP requests.
- Custom user profiles and address information.
- Soft deletion support for user accounts.
- Unique discount codes for users.
- Discount code management and usage tracking.
- User update tracking with Django signals.

### 💬 Real-Time Customer Support

- Real-time messaging using Django Channels.
- WebSocket-based communication.
- Dedicated chat rooms for individual customers.
- Support for communication between customers and staff.
- Persistent message storage in the database.
- Message timestamps and read-status fields.

### ⚙️ API Architecture

- RESTful API development with Django REST Framework.
- Modular application structure.
- JSON-based API responses.
- Authentication and permission handling.
- Separation of account, store, and chat responsibilities.

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Django REST Framework | REST API development |
| Django Channels | Asynchronous communication and WebSocket support |
| WebSockets | Real-time messaging |
| JWT | Token-based authentication |
| PostgreSQL | Relational database, when configured |
| Django Cache Framework | Temporary OTP storage and expiration |
| Meli payamak | SMS delivery for OTP verification |
| Zarinpal | Online payment gateway |

> **Note:** The database, cache backend, JWT package, and external service configurations depend on the project's actual settings and installed dependencies.

## 🏗️ Project Structure

```text
backend/
├── accounts/
│   ├── migrations/
│   ├── models.py
│   ├── signals.py
│   └── ...
│
├── chat/
│   ├── migrations/
│   ├── middleware/
│   ├── consumers.py
│   ├── routing.py
│   └── ...
│
├── config/
│   └── settings/
│
├── store/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── ...
│
└── manage.py
```

### Application Responsibilities

| App | Responsibility |
|---|---|
| `accounts` | User accounts, OTP authentication, discount codes, and account tracking |
| `store` | Products, inventory, orders, and payment integration |
| `chat` | Chat rooms, messages, WebSocket consumers, and routing |
| `config` | Django settings and project configuration |

## 🔑 OTP Authentication Flow

The authentication system uses phone number verification instead of requiring users to log in with a traditional username and password.

```text
Client
  │
  ▼
Submit Phone Number
  │
  ▼
Send OTP via SMS
  │
  ▼
Store Hashed OTP in Cache
  │
  ▼
Submit Verification Code
  │
  ▼
Validate OTP and Expiration
  │
  ▼
Create or Retrieve User
  │
  ▼
Generate JWT Tokens
  │
  ▼
Authenticated Client
```

The implementation includes temporary OTP storage, expiration handling, verification attempt limits, and a cooldown between SMS requests.

## 💬 Real-Time Chat Architecture

The chat application uses Django Channels to establish persistent WebSocket connections between authenticated users and support staff.

```text
Customer Client                 Support Client
      │                               │
      ▼                               ▼
 WebSocket Connection            WebSocket Connection
      │                               │
      └───────────┬───────────────────┘
                  ▼
           Django Channels
                  │
                  ▼
             Chat Consumer
                  │
          ┌───────┴────────┐
          ▼                ▼
      Chat Room       Message Storage
          │                │
          └───────┬────────┘
                  ▼
          Real-Time Delivery
```

Each customer has a dedicated chat room. Messages are saved to the database and distributed through channel groups, allowing connected participants to receive messages in real time.

## 💳 Payment Integration

The store application integrates with **Zarinpal** to support online payment processing.

The payment workflow is intended to connect order registration with the external payment gateway and payment verification.

The exact payment lifecycle depends on the implementation of the payment request, callback, and verification endpoints.



## 🔌 API Modules

The backend is divided into three API modules.

| Module | Main functionality |
|---|---|
| Accounts API | OTP login, user profiles, and discount codes |
| Store API | Products, inventory, orders, and payments |
| Chat WebSocket API | Real-time customer-support messaging |


## 🔒 Security Considerations

Security is an important part of an e-commerce backend, particularly when handling authentication, customer information, and online payments.

The project includes mechanisms such as OTP expiration, verification attempt tracking, hashed OTP storage, and JWT-based authentication.

For production deployments, the following practices are recommended:

- Enable HTTPS and secure WebSocket connections.
- Configure rate limiting for OTP requests and verification attempts.
- Validate phone numbers and all incoming request data.
- Restrict administrative and staff-only operations.
- Validate WebSocket room access on the server side.
- Use environment variables for secrets and external service credentials.
- Verify payment callbacks with the payment provider before confirming an order.
- Configure Django's production security settings.

## 🐳 Docker & Deployment

The application uses **Docker Compose** to orchestrate its backend infrastructure and simplify deployment. The services run in separate containers and communicate through an internal Docker network.

### Infrastructure

| Service | Image / Technology | Responsibility |
|---|---|---|
| `web` | Custom Docker image | Runs the Django application using Uvicorn and ASGI |
| `db` | PostgreSQL 15 | Stores application data |
| `redis` | Redis 7 Alpine | Provides an in-memory data store for caching and other configured services |
| `nginx` | Nginx Alpine | Acts as a reverse proxy and handles HTTP/HTTPS traffic |

### Architecture

```text
                   Client / Browser
                          │
                          ▼
                    Nginx :80/:443
                          │
                          ▼
                 Django + Uvicorn :8000
                    ┌─────┴─────┐
                    ▼           ▼
                PostgreSQL    Redis
                   :5432       :6379
```

### Key Docker Features

- **Containerized services:** Django, PostgreSQL, Redis, and Nginx run in separate containers.
- **Docker Compose:** Defines and manages the multi-container application.
- **Persistent database storage:** PostgreSQL data is stored in a mounted volume to preserve data across container recreation.
- **Environment-based configuration:** Sensitive settings and service credentials are supplied through an environment file.
- **Health checks:** PostgreSQL readiness and Django application health are checked through configured health-check commands.
- **Reverse proxy:** Nginx forwards incoming traffic to the backend and serves configured static assets and media files.
- **ASGI support:** Uvicorn runs the Django ASGI application, enabling support for asynchronous application features.
- **Automatic restart:** Services use restart policies to improve recovery after container failures.

### Running with Docker Compose

Build and start the services:

```bash
docker compose up -d --build
```

View running containers:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f web
```

Stop the services:

```bash
docker compose down
```

> **Note:** The database files are stored in the configured host directory. Running `docker compose down` does not normally delete this bind-mounted data. Back up the database before performing maintenance or deployment changes.

## 👨‍💻 Developer

Developed as a modular backend project using Django and Django REST Framework, with an emphasis on API development, authentication, e-commerce workflows, and real-time communication.

---

<div align="center">

**Built with Django · Powered by APIs · Designed for E-Commerce**

</div>