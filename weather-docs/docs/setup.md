# Setup & Installation

Follow these steps to get the application running on your local machine.

## Prerequisites

*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
*   Git installed.

## Quick Start

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/xVeradus/Projektrealisierung.git
    cd Projektrealisierung
    ```

2.  **Start with Docker Compose**
    ```bash
    docker-compose up --build
    ```

3.  **Access the Application**
    *   Frontend: [http://localhost:8080](http://localhost:8080)
    *   Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## How to Use

1.  **Locate**: Use the map to zoom into your area of interest. 
2.  **Pin it**: Drag the blue search pin to a specific location. The search radius will update automatically.
3.  **Search**: Adjust the radius slider in the top panel and coordinates if needed, then click "Search".
4.  **Explore**: Click on any highlighted weather station marker.
5.  **Analyze**: View the temperature trends in the popup. Toggle between different periods (Annual/Seasonal) and use the year slider to focuses on specific decades.

## Troubleshooting

### Connection Failed
If the frontend says "Backend connection check failed", ensure the backend container (`weather_api`) is running healthy. The backend may take a minute on the first run to download/import the global station metadata.

### Port Conflicts
*   Frontend uses port **8080**.
*   Backend uses port **8000**.
Ensure these ports are free on your host machine.

