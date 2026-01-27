# Weather App Documentation

Welcome to the documentation for the **Weather App**, a historical weather station data viewer and analysis tool.

## Project Overview

The **Weather App** is a specialized tool designed to explore and analyze decades of historical climate data. It connects to the NOAA Global Historical Climatology Network (GHCN) to provide users with a seamless, interactive experience for visualizing temperature trends across the globe.

### ✨ Core Features

*   **📍 Spatial Discovery**:
    Explore historical weather stations in the surrounding of your current or any location using the interactive map.
*   **📈 Visual Analysis**: High-performance charts (Chart.js) that handle missing data gracefully using dashed lines to maintain visual continuity without misrepresenting gaps.
*   **:material-speedometer: Optimized Backend**: A FastAPI-powered engine utilizing SQLite for efficient local caching, Pandas for rapid data processing, and GZip compression for minimal network latency.
*   **:material-layers-outline: Modular Architecture**: Built with Angular 19 and modern UI components, emphasizing a clean "glassmorphism" aesthetic and responsive layout.
*   **:material-database-sync: Smart Data Ingestion**: Lazy-loading strategy that fetches and aggregates daily climate records on-demand, ensuring the system remains lightweight yet comprehensive.

## Navigation

*   **[Architecture](architecture.md)**: High-level overview of the system components and design decisions.
*   **[Backend](backend.md)**: Details on the API, database schema, and data import processes.
*   **[Frontend](frontend.md)**: Information about the Angular application, components, and state management.
*   **[Setup & Installation](setup.md)**: Guide to getting the application running locally using Docker.
