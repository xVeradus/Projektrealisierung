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

```html
<div class="layout">
  <app-settings-configuration class="sidebar"></app-settings-configuration>
  <app-map-view class="main-map"></app-map-view>
  <pop-up-display [visible]="ui.showDialog()" ...></pop-up-display>
</div>
```
