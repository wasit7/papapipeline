# Tutorial 07: End-to-End Real-Time Data Pipeline with Prefect 3 and lakeFS

## Project Overview
Welcome to **Tutorial 07** of the `papapipeline` repository, designed to guide students in building an end-to-end real-time data pipeline. This tutorial extends the concepts from earlier tutorials (e.g., `tutorial03`) by empowering you to design a custom pipeline that collects data every 15 minutes from a chosen source, orchestrates it using **Prefect 3**, stores it in a **lakeFS** data lake via S3A protocol, and visualizes it using **Streamlit**. The tutorial emphasizes modern data engineering practices, including workflow orchestration, data lake storage, and version control with GitHub.

In this example, we use the **OpenWeatherMap API** to collect weather data (e.g., temperature, humidity, wind speed) for a city (e.g., Bangkok). You can adapt the pipeline for other data sources (e.g., Twitter API, sensor data) by modifying the schema and scripts. The tutorial aligns with the educational goals of `papapipeline`, providing hands-on experience for data science and engineering students.[](https://wasit7.medium.com/building-a-simple-prefect-3-data-pipeline-with-jupyter-and-docker-7eeac8f7df0f)[](https://wasit7.medium.com/bringing-data-science-and-engineering-to-thai-students-a-practical-prefect-3-tutorial-2ba765e297bc)

## Prerequisites
- **Python 3.8+**
- **Docker** and **Docker Compose**
- **GitHub** account with SSH access
- **OpenWeatherMap API key** (sign up at https://openweathermap.org)
- **lakeFS** instance (local or remote) with S3A credentials
- Basic knowledge of Prefect 3, Docker, and Git

## Setup Instructions
Follow these steps to set up the tutorial environment:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/wasit7/papapipeline.git
   cd papapipeline/tutorial07
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**:
   - Obtain an OpenWeatherMap API key and set it:
     ```bash
     export OPENWEATHER_API_KEY=your-api-key
     ```
   - Update lakeFS credentials in `src/pipeline.py`, `src/setup.py`, and `visualization/app.py`:
     ```python
     LAKEFS_ENDPOINT = "http://localhost:8000"
     LAKEFS_ACCESS_KEY = "your-lakefs-access-key"
     LAKEFS_SECRET_KEY = "your-lakefs-secret-key"
     LAKEFS_REPO = "student-repo"
     LAKEFS_BRANCH = "main"
     ```

4. **Run Setup Script**:
   Initialize the lakeFS repository and environment:
   ```bash
   python src/setup.py
   ```

5. **Start Docker Services**:
   Launch Prefect server and Streamlit:
   ```bash
   docker-compose up -d
   ```

6. **Deploy Prefect Flow**:
   Deploy the pipeline with a 15-minute schedule:
   ```bash
   python src/pipeline.py deploy
   ```
   This creates a deployment named `data-pipeline` in the `default-agent-pool` work pool, running every 15 minutes (`cron="*/15 * * * *"`).

## Usage
- **Prefect UI**: Monitor pipeline execution at `http://localhost:4200`.
- **Streamlit Dashboard**: View real-time data visualizations at `http://localhost:8501`.
- **lakeFS Data Lake**: Access stored data via an S3A client (endpoint: `http://localhost:8000`, repository: `student-repo`, branch: `main`).
- **GitHub Integration**:
  - Push changes to your repository:
    ```bash
    git add .
    git commit -m "Updated pipeline code"
    git push origin main
    ```
  - Ensure at least 3 commits for KPI compliance.

## Schema
The data schema is defined in `SCHEMA.md`. For the weather data example:
```python
{
    "columns": ["timestamp", "city", "temperature", "humidity", "wind_speed"],
    "types": ["TEXT", "TEXT", "REAL", "INTEGER", "REAL"],
    "key_columns": ["temperature", "humidity", "wind_speed"]
}
```
- **timestamp**: ISO format timestamp of data collection.
- **city**: City name (e.g., Bangkok).
- **temperature**: Temperature in Celsius.
- **humidity**: Humidity percentage.
- **wind_speed**: Wind speed in meters/second.

Key columns are used for data quality checks (no missing values). Adapt the schema for your data source as needed.

## Results
Upon successful completion, the pipeline:
- Collects 500+ records over 1 week (672 records at 4 records/hour × 24 hours × 7 days).
- Stores data in lakeFS as Parquet files (`main/data/`), matching the documented schema.
- Achieves 90%+ successful Prefect flow runs over 24 hours (96 runs).
- Displays real-time data in a Streamlit dashboard with a table and temperature trend chart.
- Maintains a GitHub repository with 8 files and 3+ commits, fully documented code, and a comprehensive final report.

## Troubleshooting
- **API Errors**: Verify `OPENWEATHER_API_KEY` is set correctly.
- **lakeFS Access**: Ensure lakeFS credentials and endpoint are valid. Check lakeFS server is running (`docker run -p 8000:8000 treeverse/lakefs`).
- **Docker Issues**: Confirm ports 4200 (Prefect) and 8501 (Streamlit) are free. Restart containers with `docker-compose down && docker-compose up -d`.
- **Prefect Failures**: Check Prefect UI logs for errors. Ensure the work pool (`default-agent-pool`) is active.
- **GitHub Push Errors**: Verify SSH key setup:
  ```bash
  ssh-keygen -t ed25519 -C "your_email@example.com"
  cat ~/.ssh/id_ed25519.pub
  ```
  Add the public key to GitHub (Settings → SSH Keys).

## Customization
To use a different data source (e.g., Twitter API, sensor data):
1. Update `src/pipeline.py` to fetch and process data from your source.
2. Modify `SCHEMA.md` with your schema, specifying columns, types, and key columns.
3. Adjust `visualization/app.py` to display relevant metrics and charts.
4. Update `REPORT.md` to document your data source and visualization.
5. Ensure lakeFS stores 500+ records and the pipeline runs every 15 minutes.

## Files
- `src/pipeline.py`: Prefect pipeline script for data collection, processing, and lakeFS storage.
- `src/setup.py`: Setup script to initialize environment and lakeFS repository.
- `visualization/app.py`: Streamlit script for data visualization.
- `docker-compose.yml`: Docker configuration for Prefect and Streamlit.
- `SCHEMA.md`: Data schema documentation.
- `REPORT.md`: Final project report.
- `README.md`: This file, with setup and usage instructions.
- `requirements.txt`: Python dependencies.

## Requirements
See `requirements.txt` for dependencies, including:
- `prefect==3.0.0`
- `pandas==2.2.2`
- `requests==2.31.0`
- `streamlit==1.38.0`
- `plotly==5.22.0`
- `boto3==1.34.0`
- `pyarrow==15.0.0`

## Acknowledgments
This tutorial builds on the `papapipeline` framework by Wasit Limprasert, inspired by `tutorial03`’s use of Prefect 3, Docker, and GitHub integration.[](https://wasit7.medium.com/building-a-simple-prefect-3-data-pipeline-with-jupyter-and-docker-7eeac8f7df0f)[](https://wasit7.medium.com/bringing-data-science-and-engineering-to-thai-students-a-practical-prefect-3-tutorial-2ba765e297bc)

---

**Happy Pipelining!** 🚀
