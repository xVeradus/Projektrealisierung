# Testing

**Stand:** Februar 2026  
**Testabdeckung Backend:** **92 %**  
**Erfolgreiche Tests:** **40**

Das Backend wurde mit `pytest` und `unittest.mock` getestet. Ziel war die Absicherung zentraler Funktionen in den Bereichen API, Datenimport, Datenverarbeitung und geografische Suche. Der Fokus lag dabei auf Stabilität, Datenkonsistenz und dem korrekten Verhalten bei Fehler- und Fallback-Szenarien.


### 1. API-Endpunkte & Lifecycle

Die Tests prüfen das Verhalten der FastAPI-Endpunkte sowie den Status der Anwendung während Start und Laufzeit.

*   **API-Verhalten**:
    *   Validierung korrekter Antworten und HTTP-Statuscodes.
    *   Prüfung des Umgangs mit ungültigen oder unvollständigen Eingaben.
*   **Initialisierung & Verfügbarkeit**:
    *   Absicherung des Ready-Status und der Guard-Logik während des Starts.
*   **Cache- und Fallback-Logik**:
    *   Prüfung des Zusammenspiels zwischen lokaler Datenbank und externen Datenquellen.


### 2. Metadaten-Import & Parsing

Dieser Bereich umfasst den Import und die Verarbeitung der Wetterstations-Metadaten.

*   **Parsing**:
    *   Korrekte Verarbeitung des NOAA-Fixed-Width-Formats.
    *   Robustes Verhalten bei fehlenden oder unvollständigen Werten.
*   **Importlogik**:
    *   Effiziente Speicherung in der Datenbank.
    *   Vermeidung unnötiger Neuimporte.
*   **Ausfallsicherheit**:
    *   Prüfung von Batch-Verarbeitung sowie Download- und Fallback-Mechanismen.


### 3. Klimadaten-Verarbeitung

Die Tests sichern die Verarbeitung und Aggregation der Temperaturdaten aus externen Quellen.

*   **Datenverarbeitung**:
    *   Korrektes Laden, Filtern und Weiterverarbeiten der Wetterdaten.
*   **Aggregation**:
    *   Prüfung der Bildung von Jahres- und Saisonwerten.
*   **Datenqualität**:
    *   Bereinigung problematischer Werte vor der JSON-Ausgabe.
*   **Fallback-Verhalten**:
    *   Nutzung alternativer Datenquellen bei Fehlern im Primärabruf.


### 4. Geometrie & Geo-Suche

Dieser Testbereich deckt die geografische Suche nach Stationen ab.

*   **Distanz- und Suchlogik**:
    *   Prüfung der Haversine-Berechnung und räumlichen Vorfilterung.
*   **Koordinatenverarbeitung**:
    *   Sicherstellung korrekter Behandlung von Randfällen.
*   **Datenbankintegration**:
    *   Validierung der Suchlogik in Verbindung mit SQL-basierten Filtern.


### 5. Fazit

Die Tests decken die wichtigsten technischen und fachlichen Kernbereiche des Backends ab.

*   **Ziel der Teststrategie**:
    *   Sicherstellung von Stabilität, korrekter Datenverarbeitung und robustem Fehlerverhalten.
*   **Ergebnis**:
    *   Hohe Testabdeckung und verlässliche Absicherung zentraler Backend-Funktionen.
