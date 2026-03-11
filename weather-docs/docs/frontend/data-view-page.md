# Data View Page

Die `DataViewPageComponent` ist der Hauptcontainer der Anwendung. Sie ordnet das Layout und behandelt minimale globale UI-Logik.

## Bibliotheken & Module
*   **Angular Common**: `CommonModule`, `HttpClient`
*   **Komponenten**: `MapViewComponent`, `SettingsConfiguration`, `PopUpDisplayComponent`
*   **Provider**: `StationUiStateService` (Scoped auf diese Komponente)

## Layout-Komposition
Setzt die drei visuellen Hauptelemente der App zusammen:
1.  **Seitenleiste**: `app-settings-configuration`
2.  **Hauptbereich**: `app-map-view`
3.  **Overlay**: `pop-up-display`

Das Layout basiert auf einer CSS-Grid oder Flexbox-Struktur, bei der die Settings-Komponente (`app-settings-configuration`) als statische Seitenleiste agiert, während die Karte (`app-map-view`) den restlichen Hauptbereich füllt. Das Popup (`pop-up-display`) wird dynamisch als Overlay darübergelegt, wenn es vom State-Service angefordert wird.
