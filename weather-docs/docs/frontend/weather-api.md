# Weather API Service

Die zentrale Kommunikationsschicht für alle Backend-Interaktionen.

## Bibliotheken & Module
*   **Angular HttpClient**: Für RESTful-Anfragen.
*   **RxJS**: `Observable` für asynchrone Datenverarbeitung.

## Endpunkte

### `searchStations(req: StationSearchRequest)`
*   **Methode**: `POST`
*   **Endpunkt**: `/api/stations/search`
*   **Beschreibung**: Sendet Lat/Lon und Radius, um nahegelegene Stationen zu finden.

### `getStationTemps(stationId: string)`
*   **Methode**: `GET`
*   **Endpunkt**: `/api/stations/{id}/temps`
*   **Beschreibung**: Ruft den kompletten historischen Temperaturdatensatz für eine spezifische Station ab.

### `ready()`
*   **Methode**: `GET`
*   **Endpunkt**: `/api/ready`
*   **Beschreibung**: Prüft, ob die Backend-Datenbank initialisiert und bereit für Anfragen ist. Wird beim App-Start verwendet.
