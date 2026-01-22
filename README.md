# 🛠️ Projektrealisierung

## 🧩 Architecture Communication Canvas (20 Punkte)

### ✅ Vollständigkeit des Canvas (2)

* 🟢 Alle Inhalte vorhanden
* 🟢 Alle Inhalte verständlich

### 🎨 Darstellung des Canvas (2)

* 🟢 Format des Canvas angemessen
* 🟢 Alle Inhalte sichtbar

### 🎯 Abgrenzung des Werteversprechens und der Kernfunktionalität (6)

* 🟢 Werteversprechen angemessen
* 🟢 Abgrenzung zur Kernfunktionalität klar
* 🟢 Kernfunktionalität konsistent mit dem Werteversprechen

### 🧱 Alle Kernfunktionalitäten vorhanden (5)

* 🟢 Alle Kernfunktionalitäten vollständig enthalten

### ⚙️ Auflistung der Komponenten und Technologien (3)

* 🟢 Separierung in Komponenten sinnvoll
* 🟢 Beschreibung der Komponenten angemessen
* 🟢 Einsatz der Technologien je Komponente sinnvoll

### 👥 Stakeholder & Businesskontext (4)

* 🟢 Analyse von Stakeholdern sinnvoll
* 🟢 Zuordnung von Rollen zu Stakeholdern sinnvoll

### 🏢 Beschreibung des Businesskontexts (2)

* 🟢 Businesskontext angemessen beschrieben

### ⚠️ Risikomanagement & Entscheidungen (3)

* 🟢 Risiken sinnvoll analysiert (inkl. Eintrittswahrscheinlichkeit & Schadenspotenzial) (2)
* 🟢 Entscheidungen/Maßnahmen angemessen abgeleitet (1)

---

## 🧱 Produkt (80 Punkte)

### 🗄️ Funktionale Eignung – Angemessenheit der Datenhaltung (10)

* 🟢 Datenstrukturen/-schemata sinnvoll
* 🟢 Datenbanktechnologie sinnvoll
* 🟢 Cachingmechanismen angemessen eingesetzt

### 🚀 Effizienz – Laufzeitverhalten (10)

* 📊 Lighthouse-Performancescan:

  * 0 → 0 Punkte
  * 1–20 → 1 Punkt
  * 21–40 → 2 Punkte
  * 41–60 → 3 Punkte
  * 61–80 → 4 Punkte
  * 81–100 → 5 Punkte
* ⏱️ Alle Kernfunktionalitäten (bei Verfügbarkeit abhängiger Systeme) < 3 Sekunden ausführbar
* ⚡ UI reagiert bei jeder Interaktion < 0,5 Sekunden (z. B. Ladeanimation)

### 🧠 Interaktionskapazitäten – Erlernbarkeit (5)

* 🟢 Nutzbarkeit ohne Anleitung

### ♿ Interaktionskapazitäten – Inklusivität (5)

* 📊 Lighthouse-Barrierefreiheitsscan:

  * 0 → 0 Punkte
  * 1–20 → 1 Punkt
  * 21–40 → 2 Punkte
  * 41–60 → 3 Punkte
  * 61–80 → 4 Punkte
  * 81–100 → 5 Punkte

### 🧾 Interaktionskapazitäten – Selbstbeschreibung (5)

* 🟢 Ästhetik
* 🟢 Kurze Klickpfade
* 🟢 Nutzbarkeit ohne Anleitung

### 🧩 Wartbarkeit – Modularität (15)

* 🧱 Sinnvolle Codestruktur (5)
* 🔎 Verständlichkeit des Codes (6)
* 📚 Sinnvoller Einsatz von Bibliotheken (4)

### 🧪 Wartbarkeit – Testbarkeit (20)

* 🧭 Angemessene Teststrategie (3)
* 📈 Testabdeckung: *(x % / 10 = y Punkte)*
* 🧩 Angemessener Einsatz von Mocking/Stubbing (4)
* 🧾 Verständlichkeit der Tests (3)

### 🛠️ Flexibilität – Installierbarkeit (10)

* 🤖 CI/CD-Pipeline mit GitHub Actions
* 🐳 Containerimages bauen & in GitHub Container Registry ablegen
* 📦 Bedarfsgerechte Verwendung von Open-Source-Containerimages
* 🧾 Erstellung einer Installationskonfiguration

---

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
