# Frontend Documentation

The frontend is a Single Page Application (SPA) built with **Angular 19** and styled with **PrimeNG**.

## Structure

```
weather-app/
├── src/
│   ├── app/
│   │   ├── data-view-page/       # Main container component
│   │   ├── map-view/             # Leaflet map component
│   │   ├── settings-configuration/# Search & filter form
│   │   ├── pop-up-display/       # Chart popup component
│   │   ├── loading-screen/       # Global loading indicator
│   │   └── weather-api.service.ts# HTTP client service
│   └── styles.css                # Global styles
```

## Key Components

### Map View (`map-view`)
*   Uses **Leaflet** to render the map.
*   Handles drag-and-drop interactions for the search pin.
*   Visualizes search radius and search results (stations) as markers.
*   Communiates with the global state via `StationUiStateService`.

### Data View Page (`data-view-page`)
*   The main layout component.
*   Integrates the Settings, Map, and Popup components.
*   Displays the "Quote of the day" (or error messages) in the header.

### Pop-up Display (`pop-up-display`)
*   **Intelligent Visualization**: Automatically detects gaps in historical data. Continuous periods with missing values are visualized as **Dashed Lines** to bridge the gap without misrepresenting the data as a single continuous period.
*   **Interactive Controls**: Filter by Year Range (Slider) and Season (Dropdown).
*   **Layout Stability**: Implements a 350ms calibration delay after the Dialog opens to ensure Chart.js calculates dimensions correctly *after* the CSS animation completes, preventing layout "jumping".

## State Management

The application leverages **Angular Signals** for reactive state management, providing a performant alternative to legacy RxJS patterns where appropriate.

### `StationUiStateService`
Acts as the central "Source of Truth" for:
*   **Map Geometry**: The current search radius and central pin location.
*   **Results Collection**: The list of stations returned from the spiritual search.
*   **Contextual Selection**: The currently active station for detail view.

## Visual Design

*   **Glassmorphism**: A core aesthetic choice. Control panels use semi-transparent backgrounds with backdrop filters and subtle borders for a modern, layered feel.
*   **PrimeNG V19**: Provides the foundation for interactive components like the Range Slider, Dialogs, and Select menus.
*   **Responsiveness**: Uses flexbox and media queries to adapt from desktop monitors to smaller tablet views.
