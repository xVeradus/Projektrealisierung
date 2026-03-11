## 🚀 Setup & Installation (Schnellstart)

### Voraussetzungen
*   **Docker** & **Docker Compose** müssen installiert sein.

### Installation
1.  **Repository klonen**:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Container starten**:
    ```bash
    docker-compose up --build
    ```

### Was passiert im Hintergrund?
*   **Backend**: Der Python-Server startet automatisch, erstellt die SQLite-Datenbank und lädt die notwendigen Basisdaten herunter, falls diese nicht vorhanden sind.
*   **Frontend**: Die Angular-App wird gebaut und über einen optimierten Nginx-Server bereitgestellt.
*   **Ready!**: Die App ist unter **http://localhost:8080** erreichbar.

---

Dokumentation: https://xveradus.github.io/Projektrealisierung/
