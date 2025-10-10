# LinkLoom: High-Performance URL Shortener

LinkLoom is a robust, high-performance backend service for shortening URLs, built with FastAPI and a modern, scalable architecture. It provides instant redirection while capturing detailed click analytics asynchronously, ensuring a seamless user experience without compromising on data collection. The entire application is containerized with Docker for consistent, portable, and rapid deployment.

---

## 🚀 Features

- **URL Shortening**: Generate a unique, random 6-character alphanumeric code for any valid URL.
- **High-Speed Redirection**: Utilizes HTTP `307 Temporary Redirect` for fast and efficient redirection to the original URL.
- **Asynchronous Click Analytics**: All click data (IP address, user-agent, referrer) is logged in the background using a Celery task queue, ensuring zero delay for the end-user.
- **Statistics Tracking**: Dedicated endpoint to retrieve detailed analytics for each short link, including total clicks and a list of the most recent click events.
- **Soft Deletion**: Links can be deactivated without being permanently deleted, preserving all historical analytics data.

---

## 🛠️ Technologies Used

| Technology         | Role & Justification                                                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Python 3.11**    | The core programming language for its readability, robust libraries, and strong community support.                                                |
| **FastAPI**        | Modern, high-performance web framework with native async support and automatic OpenAPI/Swagger docs.                                              |
| **PostgreSQL**     | Primary relational database, chosen for its reliability, data integrity, and advanced query capabilities.                                         |
| **SQLAlchemy**     | ORM for managing database interactions in a Pythonic way.                                                                                        |
| **Pydantic**       | Ensures robust data validation, serialization, and settings management.                                                                          |
| **Celery & Redis** | **Celery** handles background click logging tasks. **Redis** acts as the message broker for Celery, enabling non-blocking, fast operations.       |
| **Pytest**         | Automated test framework for reliable, scalable tests and regression prevention.                                                                 |
| **Docker**         | Containerizes the app and its dependencies (PostgreSQL, Redis) for consistent, isolated, and reproducible environments.                          |

---

## 🏁 Getting Started

This project is fully containerized. You only need Docker to get started.

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/)

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/Pranavchikte/url-shortener-backend.git
    cd url-shortener-backend
    ```

2. **Configure Environment Variables:**

    The project uses a `.env` file for local configuration. By default, this is handled automatically by `docker-compose.yml`. No manual setup is required for the default configuration.

### Running the Application

1. **Build and run the containers:**

    From the root directory, execute:

    ```bash
    docker-compose up --build
    ```

    This will build the Docker image and start all services (web server, worker, database, Redis).

2. **Access the Application:**

    - The API is available at [http://localhost:8000](http://localhost:8000)
    - Interactive API documentation (Swagger UI) at [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Stopping the Application:**

    Press `Ctrl+C` in the terminal and then run:

    ```bash
    docker-compose down
    ```

---

## 📚 API Endpoints

For detailed request/response models, see the interactive documentation at `/docs`.

| Method | Endpoint                | Description                                   |
|--------|------------------------|-----------------------------------------------|
| POST   | `/api/shorten`         | Creates a new short URL from an original URL. |
| GET    | `/{short_code}`        | Redirects to the original URL.                |
| GET    | `/api/stats/{short_code}` | Retrieves analytics for a specific short URL. |
| GET    | `/health`              | Checks the health of the application and DB.  |

---

## 🧪 Running Tests

Tests are run using `pytest` inside the Docker container for a consistent environment.

1. Ensure your application containers are running:

    ```bash
    docker-compose up
    ```

2. In a new terminal, execute:

    ```bash
    docker-compose exec web pytest
    ```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new feature branch:

    ```bash
    git checkout -b feature/amazing-feature
    ```

3. Commit your changes:

    ```bash
    git commit -m 'feat: Add some amazing feature'
    ```

4. Push to the branch:

    ```bash
    git push origin feature/amazing-feature
    ```

5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
