
# TestRunner Application

## Overview

TestRunner is a web application designed to execute Selenium-based regression tests on different environments. The application is containerized using Docker and Docker Compose for easy deployment and scalability.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

### Clone the Repository

First, clone the repository to your local machine:

\`\`\`bash
git clone https://github.com/yourusername/TestRunnerApp.git
cd TestRunnerApp
\`\`\`

### Setting Up Docker

Ensure you have Docker and Docker Compose installed on your machine. If not, follow the official installation guides:

- [Docker Installation](https://docs.docker.com/get-docker/)
- [Docker Compose Installation](https://docs.docker.com/compose/install/)

### Build and Run the Application

1. **Build the Docker images and start the containers**:

    \`\`\`bash
    docker-compose up --build
    \`\`\`

    This command will:
    - Build the Docker images for the application and Selenium.
    - Start the containers for the application (`testrunner`), Selenium (`selenium`), and NGINX (`nginx`).

2. **Access the Application**:

    Once the containers are up and running, you can access the TestRunner application in your web browser at:

    \`\`\`plaintext
    http://localhost/testrunner
    \`\`\`

## Configuration

### Docker Compose Configuration

The \`docker-compose.yml\` file defines the services and networks for the application. Here is an example configuration:

\`\`\`yaml
version: '3.8'

networks:
  report_network:
    external: true

services:
  selenium:
    image: selenium/standalone-chrome:latest
    container_name: selenium
    ports:
      - "4444:4444"
    shm_size: '2gb'
    networks:
      - report_network

  testrunner:
    build: .
    container_name: testrunner
    ports:
      - "5000:5000"
    depends_on:
      - selenium
    volumes:
      - .:/app
    environment:
      - SELENIUM_URL=http://selenium:4444/wd/hub
    networks:
      - report_network

  nginx:
    image: nginx:latest
    container_name: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    networks:
      - report_network
\`\`\`

### Environment Variables

- \`SELENIUM_URL\`: URL of the Selenium server, which is set to \`http://selenium:4444/wd/hub\`.

### NGINX Configuration

The \`nginx.conf\` file defines the reverse proxy settings to route requests to the \`testrunner\` service:

\`\`\`nginx
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;

        location /testrunner {
            proxy_pass http://testrunner:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
\`\`\`

## Running Tests

The application will automatically run the configured Selenium tests when you start the containers. You can trigger tests through the web interface.

## Contributing

Please follow the [contributing guidelines](CONTRIBUTING.md) if you wish to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
