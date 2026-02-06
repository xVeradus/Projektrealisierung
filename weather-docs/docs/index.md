# Wetter-App Dokumentation

Willkommen in der Dokumentation der **Weather App**, einem revolutionären Tool zur Anzeige und Analyse historischer Wetterstationsdaten.

## Projektübersicht

Die **Weather App** ist ein spezialisiertes Tool zur Erkundung und Analyse jahrzehntelanger historischer Klimadaten. Sie verbindet sich mit dem NOAA Global Historical Climatology Network (GHCN), um Nutzern eine nahtlose, interaktive Erfahrung zur Visualisierung von Temperaturtrends auf der ganzen Welt zu bieten.

### ✨ Kernfunktionen

*   **📍 Immersive Räumliche Entdeckung**:
    Tauche ein in die Welt der historischen Klimadaten. Erkunde nahtlos Wetterstationen in deiner unmittelbaren Umgebung oder an jedem beliebigen Ort des Globus durch unsere hochresponsive, interaktive Karten-Schnittstelle.
*   **📈 Präzisions-Visualisierung**: Erlebe Datenvisualisierung auf neuem Niveau. Unsere High-Performance-Charts rendern Jahrzehnte an Daten in Millisekunden und schließen Datenlücken intelligent und ästhetisch anspruchsvoll, um ein unverfälschtes Bild der klimatischen Historie zu zeichnen.
*   **⚡ High-Velocity Backend Engine**: Angetrieben von einer hochoptimierten FastAPI-Architektur. Wir nutzen SQLite für blitzschnelles lokales Caching und Pandas für Datenverarbeitung in Echtzeit – maximale Effizienz für minimale Latenz.
*   **💎 Ästhetische Modulare Architektur**: Ein Meisterwerk moderner Webentwicklung, realisiert mit Angular 19. Das Design folgt strengen "Glassmorphism"-Prinzipien und bietet eine luxuriöse, responsive Benutzeroberfläche, die auf jedem Gerät glänzt.
*   **🔄 Intelligente On-Demand Ingestion**: Eine fortschrittliche Lazy-Loading-Strategie, die globale Klimadatensätze nur bei Bedarf abruft und dynamisch aggregiert. Das System bleibt federleicht, während es Zugriff auf ein massives Datenuniversum bietet.

## Navigation

*   **[Architektur](architecture.md)**: High-Level-Überblick über die Systemkomponenten und Designentscheidungen.
*   **[Backend](backend/index.md)**: Details zur API, dem Datenbankschema und den Datenimportprozessen.
*   **[Frontend](frontend/index.md)**: Informationen über die Angular-Anwendung, Komponenten und das State Management.
*   **[Einrichtung & Installation](setup.md)**: Anleitung zur lokalen Ausführung der Anwendung mit Docker.
