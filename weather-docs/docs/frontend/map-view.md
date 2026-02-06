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

```typescript
    effect(() => {
      const stations = this.ui.stations();
      if (!this.map) return;
      this.renderStations(stations);
    });
```

### Drag & Drop Suche
Implementiert die HTML5 Drag & Drop API, damit der Nutzer einen "Pin" aus der Seitenleiste auf die Karte ziehen kann.
*   **Drag Over**: Berechnet den potenziellen Suchradius basierend auf dem aktuellen Zoom-Level und rendert einen "Vorschau-Kreis".
*   **Drop**: Aktualisiert den globalen `center`-State im `StationUiStateService` mit den neuen Koordinaten und dem Radius, was eine neue Suche auslöst.

### Radius-Berechnung
Berechnet dynamisch einen "sinnvollen" Suchradius basierend auf dem aktuellen Kartenausschnitt (Viewport), um sicherzustellen, dass der Nutzer immer einen relevanten Bereich relativ zu seinem Zoom-Level durchsucht.

```typescript
  private getRadiusFromZoom(): number {
    // ... berechnet Radius basierend auf Viewport-Breite/Höhe
    return Math.max(1, radiusInKm);
  }
```
