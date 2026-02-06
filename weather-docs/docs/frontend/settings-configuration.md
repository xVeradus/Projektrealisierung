# Settings Configuration (Einstellungen)

Die `SettingsConfiguration`-Komponente stellt das Formular in der Seitenleiste bereit, um die Suchparameter zu steuern.

## Bibliotheken & Module
*   **Angular ReactiveForms**: `FormBuilder`, `FormGroup`, `Validators`.
*   **PrimeNG**: `InputNumber`, `Slider`, `DatePicker`, `ToggleSwitch`.

## Logik

### Formular-Synchronisation
Das Formular ist bidirektional mit dem globalen `StationUiStateService` synchronisiert.
*   **UI zu State**: Wenn der Nutzer Eingaben ändert, wird `searchStations()` aufgerufen, was den globalen State aktualisiert und die API triggert.
*   **State zu UI**: Wenn der Nutzer einen Pin auf die Karte droppt, aktualisiert sich der State, und ein `effect()` in dieser Komponente aktualisiert die Formularwerte (Lat/Lon), damit sie übereinstimmen.

### Range Slider (Bereichsregler)
Ein Schieberegler mit zwei Griffen ermöglicht die Auswahl eines Jahresbereichs (z.B. 1950-2023).

### Such-Trigger
Ruft den `WeatherApiService` auf, um passende Stationen abzurufen.

```typescript
    this.api.searchStations(req).subscribe({
      next: (stations) => {
        this.ui.setStations(stations); // Push in den globalen State
      }
    });
```
