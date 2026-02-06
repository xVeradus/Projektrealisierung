# Loading Screen

Behandelt globale Ladezustände, um während asynchroner Operationen visuelles Feedback zu geben.

## Bibliotheken & Module
*   **Angular Interceptor**: `HttpInterceptor` (impliziert durch Architektur).
*   **Signals**: Für reaktive UI-Updates.

## Komponenten

### LoadingService
Ein Singleton-Service, der einen Referenzzähler aktiver Anfragen verwaltet.
*   `show()`: Erhöht den Zähler.
*   `hide()`: Verringert den Zähler.
*   `isLoading$`: Observable, das `true` sendet, wenn der Zähler > 0 ist.
Dies ermöglicht es, dass mehrere parallele Anfragen den Ladebildschirm aktiv halten, bis *alle* beendet sind.

### LoadingOverlay
Die visuelle Komponente, die den `LoadingService` abonniert. Sie zeigt typischerweise einen Spinner oder Ladebalken über dem gesamten Bildschirm an und verhindert Interaktionen, solange kritische Daten laden.
