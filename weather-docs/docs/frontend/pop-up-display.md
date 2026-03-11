# Pop-Up Display

Die `PopUpDisplayComponent` rendert individuelle Temperatur-Diagramme für ausgewählte Wetterstationen.

## Bibliotheken & Module
*   **Chart.js**: Via `primeng/chart`.
*   **PrimeNG**: `Dialog`, `Select` (Dropdown), `Slider`.

## Features

### Intelligente Visualisierung
*   **Lückenerkennung**: Das Diagramm visualisiert Datenlücken.
*   **Multi-Saison-Support**: Nutzer können spezifische Jahreszeiten (z.B. "Winter", "Sommer") auswählen.
*   **Dynamische Farben**: Jede Saison hat eine definierte Farbpalette.


### Daten-Caching
Implementiert einen lokalen Cache `rowsCache`, um Filterung (Jahresbereich, Saison) zu ermöglichen, ohne die Daten jedes Mal neu von der API abzurufen, wenn der Nutzer die UI-Regler bedient.
