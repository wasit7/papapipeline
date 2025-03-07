# **Chapter 2: Docker and Docker Compose**

## **2.1 Introduction to Containerization**

### 2.1.1 Why Containers?
**Containers** provide a way to package software with all its dependencies in a self-contained environment. Unlike virtual machines, containers share the host’s OS kernel and therefore are typically more lightweight and faster to start.

**Key benefits:**
1. **Portability**: Containers run the same way across different environments.  
2. **Isolation**: Each container has its own filesystem, dependencies, and processes.  
3. **Scalability**: You can easily spin up multiple containers to handle increased load.

### 2.1.2 Docker as a Container Platform
**Docker** is the most widely used platform for containerization. It provides:
- Tools for **building** container images (via **Dockerfiles**).
- Commands to **run** containers locally.
- A registry (Docker Hub) to **push/pull** images.

---

## **2.2 Docker Images vs. Containers**

- **Docker Image**  
  - A **read-only template** that defines what goes inside the container (OS, libraries, dependencies, and application code).  
  - Typically stored in a repository (local or remote like Docker Hub).
- **Docker Container**  
  - A **running instance** of an image.  
  - Can be started, stopped, and removed.  
  - Multiple containers can share the same underlying image.

### 2.2.1 Common Docker Images
- Official base images: `ubuntu`, `python`, `node`, etc.  
- Application-specific images: `prefecthq/prefect`, `postgres`, `nginx`, etc.

---

## **2.3 Building Images with a Dockerfile**

### 2.3.1 Dockerfile Overview
A **Dockerfile** is a plain text file containing **instructions** that define how to build your image.

**Common instructions**:
1. **`FROM <base-image>`**: Specifies the starting image layer.  
2. **`COPY <src> <dest>`**: Copies files from host to the container’s file system.  
3. **`RUN <command>`**: Executes a command (install packages, set up tools) while building the image.  
4. **`CMD`** or **`ENTRYPOINT`**: Defines the default command to run when the container starts.

Example **Dockerfile** snippet:
```dockerfile
# Start from official Python image
FROM python:3.11-slim

# Copy local code into the container
COPY . /app

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["python", "hello_flow.py"]
```

### 2.3.2 Building and Tagging the Image
Use `docker build` to create an image from a Dockerfile:
```bash
docker build -t my-python-app .
```
- `-t` sets the **tag** (name) of the image (`my-python-app`).  
- The `.` at the end indicates the **build context** (current directory).

---

## **2.4 Essential Docker Commands**

### 2.4.1 Pulling and Running Images
- **`docker pull <image>`**  
  Fetches a Docker image from a registry like Docker Hub.
- **`docker run <image>`**  
  Creates and starts a container from `<image>`.

### 2.4.2 Listing and Stopping Containers
- **`docker ps`**  
  Lists all running containers (add `-a` to show **all** containers, including stopped ones).
- **`docker stop <container-id>`**  
  Stops a running container gracefully.
- **`docker rm <container-id>`**  
  Removes a stopped container from your system.

### 2.4.3 Viewing Logs
- **`docker logs <container-id>`**  
  Displays logs from the container’s standard output. Useful for debugging.

### 2.4.4 Accessing a Container Shell
- **`docker exec -it <container-id> bash`**  
  Launches an interactive shell within a running container for debugging or manual commands.

---

## **2.5 Docker Compose Fundamentals**

### 2.5.1 Why Use Docker Compose?
**Docker Compose** solves the challenge of running multiple containers (services) together, each of which may represent a different component of your application (e.g., a web server, a database, a queue). Compose:

1. **Orchestrates** multiple services using a single YAML file (`docker-compose.yml`).  
2. **Automates networking** between containers.  
3. Makes it easy to **scale** services horizontally (e.g., multiple worker replicas).

### 2.5.2 The docker-compose.yml File
A typical `docker-compose.yml` has the following structure:
```yaml
version: '3.9'
services:
  web:
    build: .
    ports:
      - "8080:80"
    volumes:
      - .:/app
    networks:
      - my-network
  
  database:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=myuser
      - POSTGRES_PASSWORD=mypassword
      - POSTGRES_DB=mydatabase
    networks:
      - my-network

networks:
  my-network:
```
**Key sections**:
- **`services:`**: Lists each containerized service.  
- **`image:`** or **`build:`**: Tells Docker Compose either to pull an image or build from a Dockerfile.  
- **`ports:`**: Expose container ports to the host (e.g., `8080:80` means host:container).  
- **`environment:`**: Pass environment variables to the container.  
- **`volumes:`**: Mount directories or named volumes.  
- **`networks:`**: Define custom networks for inter-service communication.

---

## **2.6 Using Docker Compose**

### 2.6.1 Starting and Stopping Services
- **`docker compose up --build`**  
  Builds images (if needed) and starts all defined services.  
- **`docker compose down`**  
  Stops and removes containers, networks, and other resources created by `docker-compose.yml`.

### 2.6.2 Listing Services and Logs
- **`docker compose ps`**  
  Shows which services are running.  
- **`docker compose logs`**  
  Displays logs for all running containers (add `-f` to follow logs in real-time).

### 2.6.3 Scaling Services
You can scale a service to run multiple containers (replicas):
```yaml
services:
  worker:
    build: .
    deploy:
      mode: replicated
      replicas: 3
```
Or from the CLI:
```bash
docker compose up --scale worker=3
```
This is particularly useful when you want to handle **high load** or parallel tasks (e.g., multiple Prefect workers).

---

## **2.7 Managing Data with Volumes**

### 2.7.1 Named Volumes
**Named volumes** allow data to **persist** even if the container is removed. For example:
```yaml
volumes:
  db_data:
```
Then use it in a service:
```yaml
services:
  database:
    image: postgres:13-alpine
    volumes:
      - db_data:/var/lib/postgresql/data
```
This ensures your Postgres data is not lost when the container restarts.

### 2.7.2 Bind Mounts
A **bind mount** links a local directory or file on the host to a path in the container. This is common for **development**:
```yaml
services:
  jupyter:
    volumes:
      - ./work:/home/jovyan/work
```
Changes made on the host system are instantly reflected in the container and vice versa.

---

## **2.8 Networking in Docker Compose**

### 2.8.1 Default Bridge Network
By default, Docker Compose creates a **bridge network** for services within the same `docker-compose.yml`. Each service can be accessed by **service name** instead of an IP address (e.g., `database:5432`).

### 2.8.2 Custom Networks
You can define multiple named networks if you want to **isolate** some services from others or connect them in more complex topologies.

---

## **2.9 Best Practices for Docker and Compose**

1. **One Service per Container**: Keep each container’s purpose clear (database, worker, web server, etc.).  
2. **Use `.dockerignore`**: Similar to `.gitignore`, it ensures large or unnecessary files don’t get copied into your build context.  
3. **Tagging and Versioning**: Use meaningful tags (e.g., `myapp:1.0.0`) for reproducibility.  
4. **Environment Variables**: Store secrets or config in environment variables or external secrets storage—avoid hardcoding them in images.  
5. **Minimize Image Size**: Use smaller base images (e.g., `python:3.11-slim`) to reduce build times and overhead.

---

## **Summary**

In this chapter, we explored the **foundations of Docker**—what images and containers are, and how to build and run them—then progressed to **Docker Compose**, which orchestrates multi-container environments. These concepts are pivotal for local or production deployments involving multiple services (e.g., a **Prefect Server** with a **Postgres** database and multiple **Prefect workers**).

In the next chapters, you’ll see **Docker** and **Docker Compose** in action with **Prefect**. We’ll learn how to run a **Prefect Server** in one container, set up a **database** for state management in another, and deploy **workers** to execute your data pipelines.

---

### **Key Takeaways**
- **Docker Images vs. Containers**: An image is a static blueprint; a container is the running instance.  
- **Dockerfile**: A script that defines how to build your image (including base OS, dependencies, and code).  
- **Docker Compose**: Simplifies multi-container setups with a single YAML file, supporting volumes, networks, and scaling.  
- **Persistence**: Named volumes ensure data isn’t lost across container restarts.  
- **Networking**: Each service can refer to others by name, making multi-service applications straightforward to configure.

With Docker and Docker Compose now covered, we’ll move to **Chapter 3: Prefect Server**, diving deeper into self-hosting the Prefect orchestration platform and connecting it to a database.