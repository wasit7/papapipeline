Below is a **step-by-step tutorial** that demonstrates how to:

1. Spin up **Postgres**, **CloudBeaver**, and **Jupyter Lab** containers using **Docker Compose**.  
2. Create a **Jupyter Notebook** that writes a simple dataset to Postgres.

This will form the foundation for your course’s **Big Data Infrastructure** setup.

---

# **Tutorial 1: Docker Compose Basics (Postgres + CloudBeaver + Jupyter Lab)**

## **1. Project Structure**

Create a new folder (for example, `big-data-infra`) on your local machine and place these files:

```
big-data-infra/
 ┣━ docker-compose.yml
 ┗━ (Jupyter notebooks will be saved in the Jupyter container volume)
```

We will keep all our configuration in `docker-compose.yml` for convenience.

---

## **2. Docker Compose Configuration**

Below is a **complete** `docker-compose.yml` that sets up three services:

1. **Postgres** – A lightweight database server.  
2. **CloudBeaver** – A web-based database administration UI for Postgres.  
3. **Jupyter Lab** – An interactive environment for Python notebooks.

```yaml
version: '3.8'

volumes:
  cloudbeaver: {}
  db: {}
  notebooks: {}  # volume to persist notebooks

services:
  postgres:
    container_name: postgres
    image: postgres:17.0-alpine
    volumes:
      - db:/var/lib/postgresql/data
    ports:
      - 5432:5432
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres-password

  cloudbeaver:
    container_name: cloudbeaver
    image: dbeaver/cloudbeaver:latest
    ports:
      - 8978:8978
    volumes:
      - cloudbeaver:/opt/cloudbeaver/workspace

  jupyter:
    container_name: jupyter
    image: jupyter/minimal-notebook:latest
    # or 'jupyter/datascience-notebook:latest' if you want more pre-installed packages
    volumes:
      - notebooks:/home/jovyan/work
    ports:
      - 8888:8888
    # Disable token authentication for simplicity (do this only in dev environments!)
    command: start-notebook.sh --NotebookApp.token=''
```

### **Key Points**

- **Volumes**  
  - `db` persists Postgres data, ensuring your data remains intact even if the container restarts.  
  - `cloudbeaver` stores configuration/workspace for CloudBeaver.  
  - `notebooks` stores Jupyter notebooks so that they’re not lost after a container stop/restart.

- **Ports**  
  - **5432** for Postgres (the default Postgres port).  
  - **8978** for CloudBeaver’s web interface.  
  - **8888** for Jupyter Lab’s interface.

- **Environment Variables** for Postgres:  
  - `POSTGRES_DB`: Name of the default database (postgres).  
  - `POSTGRES_USER`: Username (postgres).  
  - `POSTGRES_PASSWORD`: Password (postgres-password).

---

## **3. Start Your Services**

In your terminal, navigate to the `big-data-infra` directory where `docker-compose.yml` is located, then run:

```bash
docker compose up -d
```

This command will:

- Pull the images if they are not already on your system.  
- Create and start the containers in detached mode (`-d`).

After a few moments, confirm everything is running:

```bash
docker ps
```

You should see three containers (`postgres`, `cloudbeaver`, `jupyter`) in the list.

---

## **4. Verify CloudBeaver**

Open your browser and go to:

```
http://localhost:8978
```

CloudBeaver should be accessible. You can **create** or **manage connections** to your Postgres database. By default, you can connect with:

- **Host**: `postgres` (because Docker’s internal network uses service names) or `localhost` if you are connecting from your **host machine** via port 5432.  
- **Database**: `postgres`  
- **User**: `postgres`  
- **Password**: `postgres-password`

*(If you want to connect to Postgres from your host machine’s SQL client, you can also use `localhost:5432`.)*

---

## **5. Access Jupyter Lab**

Open your browser and go to:

```
http://localhost:8888
```

You should see the **Jupyter Lab** interface. Since we disabled token authentication (for simplicity), you’ll be taken directly to the notebook dashboard.

> **Security Note**: Disabling token auth is convenient in a local development environment but is **not recommended** for production.

---

## **6. Create a Notebook to Write Data into Postgres**

Inside Jupyter Lab, create a **new Python notebook** (e.g., `tutorial_1.ipynb`) in the `work` directory.  
   
### **6.1 Install Required Python Packages**  

Because the `jupyter/minimal-notebook` image is quite bare, you may need to install packages like `sqlalchemy`, `psycopg2`, and `pandas`. In a notebook cell, run:

```python
!pip install sqlalchemy psycopg2-binary pandas
```

> If you use the `jupyter/datascience-notebook` image, `pandas` might already be included, but you’ll still need `sqlalchemy` and `psycopg2-binary`.

### **6.2 Notebook Code Example**

Below is an example notebook cell to create a simple dataset and save it to Postgres. This uses **SQLAlchemy** to handle database connections and **pandas**’ `to_sql` function for writing data:

```python
import pandas as pd
from sqlalchemy import create_engine

# Use the Postgres service name ("postgres") for 'host' 
# in Docker's default network so the Jupyter container can resolve it.
HOST = 'postgres'  
USERNAME = 'postgres'
PASSWORD = 'postgres-password'
POSTGRES_PORT = 5432
DB_NAME_POSTGRES = 'postgres'

def connect_postgres():
    """
    Creates a SQLAlchemy engine for Postgres.
    """
    postgres_url = f'postgresql://{USERNAME}:{PASSWORD}@{HOST}:{POSTGRES_PORT}/{DB_NAME_POSTGRES}'
    return create_engine(postgres_url)

def save_to_postgres(df, table_name):
    """
    Saves a pandas DataFrame to a specified table in Postgres.
    If the table already exists, it will be replaced.
    """
    engine = connect_postgres()
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Data saved to PostgreSQL table: {table_name}")

# 1. Create a simple dataset
your_df = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie']
})

# 2. Write DataFrame to Postgres
save_to_postgres(your_df, 'your_table')
```

**What’s happening here?**

1. **connect_postgres()** – Creates a connection string using the Postgres username, password, host, port, and database name.  
2. **save_to_postgres(df, table_name)** – Writes a pandas DataFrame (`df`) to the specified table. We use `if_exists='replace'` to recreate the table each time.  
3. We create a **DataFrame** (`your_df`) with dummy data.  
4. Finally, we call **`save_to_postgres()`** to insert that data into the `your_table` table in Postgres.

---

## **7. Verify the Data in Postgres**

### **Option A: Using CloudBeaver**

1. In CloudBeaver at `http://localhost:8978`, ensure you have a **Postgres** connection.  
2. Under the **public schema**, look for the newly created table `your_table`.  
3. Right-click the table, choose “View Data” or “Read Data in SQL Console,” and you should see the rows inserted by your notebook.

### **Option B: Using `psql` (optional)**

If you have `psql` installed on your host machine:

```bash
psql -h localhost -p 5432 -U postgres -d postgres
Password for user postgres: postgres-password

# Then run:
SELECT * FROM your_table;
```

You should see the three rows from your DataFrame.

---

## **8. Stopping and Cleaning Up**

When you’re done, you can stop your containers:

```bash
docker compose down
```

- Your data in **Postgres** and your notebooks in **Jupyter** will **remain saved** in the Docker volumes (`db` and `notebooks`) unless you remove them explicitly by running:

```bash
docker compose down -v
```

*(This permanently deletes the volumes and all stored data.)*

---

# **Summary & Next Steps**

- You now have a **basic big data environment** with **Postgres** (database), **CloudBeaver** (web-based DB UI), and **Jupyter Lab** (interactive notebooks).
- You practiced **writing** data into Postgres from a Jupyter notebook.

### **Up Next**
1. **Data Ingestion & Integration**: Learn how to pull data from logs, APIs, or other sources into Postgres.  
2. **Advanced Queries**: Explore SQL features or tools like **Ibis** for analytics.  
3. **Data Versioning**: Add LakeFS and Parquet for advanced data management.  
4. **Workflow Orchestration**: Introduce Prefect to automate your data pipelines end-to-end.

Stay tuned for the next tutorial as we build upon this foundation to integrate additional tools and data sources in your **Big Data Infrastructure** course!

---

### **Troubleshooting Tips**

- If Jupyter can’t connect to Postgres with `HOST = 'postgres'`, confirm your services are on the **same Docker network** (they are by default in the same compose file).  
- Always check container logs (e.g., `docker logs postgres`) for helpful error messages if something goes wrong.  
- Make sure you don’t have a local Postgres instance on port 5432 conflicting with the Docker one. You can change the mapped port in `docker-compose.yml` if needed (e.g., `5433:5432`).  

Feel free to modify any version, port, or environment variable settings to suit your local setup. **Happy coding** and see you in the next tutorial!