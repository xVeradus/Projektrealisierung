# Einrichtung & Installation

Folge diesen Schritten, um die Anwendung lokal auszuführen.

## Voraussetzungen

*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert und gestartet.
*   Git installiert.

## Schnellstart

1.  **Repository klonen**
    ```bash
    git clone https://github.com/xVeradus/Projektrealisierung.git
    cd Projektrealisierung
    ```

2.  **Start mit Docker Compose**
    ```bash
    docker-compose up --build
    ```

3.  **Zugriff auf die Anwendung**
    *   Frontend: [http://localhost:8080](http://localhost:8080)
    *   Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Bedienung

1.  **Navigieren**: Nutze die Karte, um in dein Zielgebiet zu zoomen.
2.  **Markieren**: Ziehe den blauen Pin an den gewünschten Ort. Der Suchradius passt sich automatisch an.
3.  **Suchen**: Passe ggf. den Radius-Slider und die Koordinaten an und klicke auf "Suchen".
4.  **Erkunden**: Klicke auf eine der hervorgehobenen Wetterstationen.
5.  **Analysieren**: Betrachte die Temperaturverläufe im Popup. Wechsle zwischen Zeiträumen (Jährlich/Saisonal) und nutze den Zeit-Slider für spezifische Jahrzehnte.
