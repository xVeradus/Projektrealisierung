# Map View

Die `MapViewComponent` ist verantwortlich für das Rendern der interaktiven Karte, die Anzeige der Stationen und die Handhabung der "Such-Pin"-Logik.

## Bibliotheken & Module
*   **Leaflet**: Die zentrale Karten-Bibliothek.
*   **Angular Core**: `Effect`, `Signal` (für reaktive Updates vom `StationUiStateService`).

## Logik

### Initialisierung
Initialisiert eine Leaflet-Karte, die auf den vom State-Service bereitgestellten Koordinaten zentriert ist.

### Reaktives Rendering
Nutzt Angular `effect()`, um auf Zustandsänderungen zu reagieren, ohne manuelle Subscription-Verwaltung:

Nutzt Angular Signals (über `effect()`), um auf Zustandsänderungen im globalen `StationUiStateService` zu reagieren. Anstatt `Subscriptions` manuell verwalten zu müssen, rendert die Karte automatisch neu, sobald sich beispielsweise das Array der Stationen (`this.ui.stations()`) ändert.
### Drag & Drop Suche
Implementiert die HTML5 Drag & Drop API, damit der Nutzer einen "Pin" aus der Seitenleiste auf die Karte ziehen kann.
*   **Drag Over**: Berechnet den potenziellen Suchradius basierend auf dem aktuellen Zoom-Level und rendert einen "Vorschau-Kreis".
*   **Drop**: Aktualisiert den globalen `center`-State im `StationUiStateService` mit den neuen Koordinaten und dem Radius, was eine neue Suche auslöst.

### Radius-Berechnung
Berechnet dynamisch einen "sinnvollen" Suchradius basierend auf dem aktuellen Kartenausschnitt (Viewport), um sicherzustellen, dass der Nutzer immer einen relevanten Bereich relativ zu seinem Zoom-Level durchsucht.

Um sicherzustellen, dass der Nutzer immer aussagekräftige Suchergebnisse erhält, wird der Suchradius basierend auf der aktuellen Zoomstufe (Viewport) berechnet. Ein weiter herausgezoomter Sichtbereich führt zu einem größeren Suchradius, wodurch irrelevante lokale Suchanfragen aus der Makroperspektive vermieden werden.
