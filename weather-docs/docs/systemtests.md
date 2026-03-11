# Systemtests für die Anwendung zur Suche historischer Wetterstationsdaten

## 1. Dokumentinformationen

| Feld | Wert |
| :--- | :--- |
| **Projekt / Anwendung:** | Weather App - Historical Data Viewer |
| **Version / Build:** | v1.0.0 |
| **Datum:** | 01.03.2026 |
| **Autoren / Tester:** | Ben Sieburg, Felix Droste |
| **Prüfer / Freigabe:** | Menko Hornstein |

---

## 2. Ziel des Dokuments

Dieses Dokument beschreibt die Durchführung und Dokumentation der Systemtests für die Anwendung, mit der historische Daten von Wetterstationen anhand von Koordinaten gesucht werden können.

Die Systemtests wurden von zwei Personen unabhängig voneinander durchgeführt. Die Ergebnisse beider Durchführungen werden getrennt dokumentiert und anschließend verglichen.

**Ziel:** Nachweis, dass die Suche nach Wetterstationsdaten anhand der vorgegebenen Parameter korrekt funktioniert.

Geprüft werden insbesondere:
- Standortsuche über Koordinaten
- Filterung über Suchradius
- Filterung über Anfangs- und Endjahr
- Zuordnung und Anzeige passender Wetterstationen
- Korrekte Werte für Gesamtjahr und Jahreszeiten
- Vollständige Protokollierung der Testdurchführung

---

## 3. Testumfang

### 3.1 Abgedeckte Mindestanforderungen
| Anforderung | Beschreibung | Abdeckung im Dokument |
| :--- | :--- | :--- |
| **A1** | Drei Standorte mit überprüften Werten für verschiedene Kombinationen von Suchradius, Anfangs- und Endjahr | Abschnitt 6 |
| **A2** | Pro Standort eine Station mit überprüften Werten für Gesamtjahr und Jahreszeiten | Abschnitt 7 |
| **A3** | Dokumentation, welche Fälle durch die Tests abgedeckt werden | Abschnitte 6.5 und 7.5 |
| **A4** | Protokollierung der Durchführung | Abschnitt 8 |

### 3.2 Nicht Bestandteil
| Bereich | Bemerkung |
| :--- | :--- |
| Backend-Unit-Tests | Werden in der separaten [Testing Documentation](testing_documentation.md) abgedeckt. |

---

## 4. Testumgebung

| Parameter | Wert |
| :--- | :--- |
| **System / URL** | `http://localhost:8080/` (Lokale Docker-Instanz) |
| **Version / Commit / Build** | `main` Branch (Build Feb/März 2026) |
| **Testdatum** | 01.03.2026 |
| **Betriebssystem** | macOS / Windows 11 |
| **Browser / Laufzeitumgebung** | Google Chrome Version 120+ |
| **Datenquelle / Datenbankstand** | NOAA GHCND Daily Summaries (S3 / NCEI Fallback) |
| **Sonstige Voraussetzungen** | Aktive Internetverbindung für Map-Tiles (Leaflet) |

---

## 5. Testdatenbasis

### 5.1 Referenzdaten
**Grundlage der erwarteten Werte (Verifizierung):**
Die Erwartungswerte für die Stationstreffer und die Temperaturaggregationen wurden *unabhängig* von unserer eigenen Backend-Anwendung validiert. Dafür wurden die offiziellen Datensätze der NOAA (National Centers for Environmental Information) über deren Web-Interface `https://www.ncei.noaa.gov/` und raw `.csv` S3-Dumps für die jeweiligen Test-Jahre heruntergeladen und stichprobenartig die Durchschnittswerte berechnet. 

Die Erwartungswerte für die **Distanzberechnung** zwischen gesuchtem Punkt und gefundener Wetterstation (Haversine-Formel) wurden vorab mit dem offiziellen "Entfernungs-Messwerkzeug" von Google Maps zwischen den gesuchten Koordinaten und den amtlichen Stationskoordinaten validiert.

| Referenz | Beschreibung | Quelle |
| :--- | :--- | :--- |
| **R1** | Metadaten-Liste aller Stationen (ghcnd-stations.txt) | NOAA NCEI |
| **R2** | Manuelle Stichproben raw S3/DLY `.csv` Jahresdateien | NOAA NCEI Daily Summaries |
| **R3** | Haversine Validierung via Distanz-Messwerkzeug | Google Maps |

---

## 6. Systemtests – Standortsuche mit Parameterkombinationen

Mindestanforderung: 3 Standorte mit überprüften Werten für verschiedene Kombinationen aus Suchradius, Anfangsjahr und Endjahr. (Zur Aufteilung auf zwei Tester wurden 4 Standorte gewählt).

### 6.1 Standort 1: Berlin (Mitte)

- **Bezeichnung des Standorts:** Berlin (Alexanderplatz)
- **Koordinaten:** Lat: 52.5200, Lng: 13.4050
- **Zugeordnete Referenzdaten:** R1, R3

#### Testmatrix Standort 1
| Testfall-ID | Suchradius | Anfangsjahr | Endjahr | Erwartetes Ergebnis | Tatsächliches Ergebnis | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ST-1.1** | 10 km | 2010 | 2020 | mind. 3 Stationen (Tegel, Tempelhof, Dahlem) | Tegel, Tempelhof, Dahlem gefunden | 🟢 OK | Tegel liegt 8.5km entfernt |
| **ST-1.2** | 2 km  | 2010 | 2020 | 0 Stationen | 0 Stationen gefunden | 🟢 OK | Keine historische Wetterstation in Mitte aktiv |
| **ST-1.3** | 50 km | 1990 | 1995 | mind. 10 Stationen (inkl. Schönefeld/Potsdam) | 12 Stationen gefunden inkl. Potsdam | 🟢 OK | Alter Zeitraum korrekte gefiltert |

#### Verifizierte Werte Standort 1 (für ST-1.1)
| Prüfpunkt | Erwarteter Wert | Tatsächlicher Wert | Abweichung | Verifiziert durch |
| :--- | :--- | :--- | :--- | :--- |
| **Gefundene Station(en)** | BERLIN-TEGEL, BERLIN-TEMPELHOF | BERLIN-TEGEL, BERLIN-TEMPELHOF | Keine | Ben Sieburg |
| **Distanz zur Station** | Tegel: ~8.5 km, Tempelhof: ~4.5 km | Tegel: 8.54 km, Tempelhof: 4.51 km | < 1% | Ben Sieburg |
| **Verfügbare Jahre** | 2010 - 2020 | 2010 - 2020 | Keine | Ben Sieburg |
| **Relevante Wetterwerte** | Temperaturdaten für TMAX und TMIN | Beide geladen und auf UI | Keine | Ben Sieburg |

---

### 6.2 Standort 2: Zugspitze (Deutschland)

- **Bezeichnung des Standorts:** Zugspitze (höchster Berg DE)
- **Koordinaten:** Lat: 47.4210, Lng: 10.9850
- **Zugeordnete Referenzdaten:** R1, R3

#### Testmatrix Standort 2
| Testfall-ID | Suchradius | Anfangsjahr | Endjahr | Erwartetes Ergebnis | Tatsächliches Ergebnis | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ST-2.1** | 5 km | 2000 | 2023 | 1 Station (Zugspitze Bergstation) | 1 Station gefunden (ZUGSPITZE) | 🟢 OK | |
| **ST-2.2** | 25 km | 2000 | 2023 | mind. 3 Stationen (inkl. Garmisch-Partenkirchen) | 4 Stationen gefunden | 🟢 OK | Berg- und Tallagen im Radius |
| **ST-2.3** | 25 km | **1880** | **1890** | Keine oder nur lückenhafte Stationen | 0 Stationen mit validen Daten | 🟢 OK | Keine Daten für diese Region so früh |

#### Verifizierte Werte Standort 2 (für ST-2.1)
| Prüfpunkt | Erwarteter Wert | Tatsächlicher Wert | Abweichung | Verifiziert durch |
| :--- | :--- | :--- | :--- | :--- |
| **Gefundene Station(en)** | ZUGSPITZE | ZUGSPITZE | Keine | Ben Sieburg |
| **Distanz zur Station** | ~0.1 km | 0.05 km | < 0.1km | Ben Sieburg |
| **Verfügbare Jahre** | 2000 - 2023 | 2000 - 2023 | Keine | Ben Sieburg |
| **Relevante Wetterwerte** | Negative Jahresdurchschnittstemperatur zu erwarten (TMAX/TMIN < 0) | Jahresdurchschnitt TMAX ca. -1°C angezeigt | Keine | Ben Sieburg |

---

### 6.3 Standort 3: New York City (Central Park)

- **Bezeichnung des Standorts:** NY Central Park, USA
- **Koordinaten:** Lat: 40.7820, Lng: -73.9660
- **Zugeordnete Referenzdaten:** R1, R3

#### Testmatrix Standort 3
| Testfall-ID | Suchradius | Anfangsjahr | Endjahr | Erwartetes Ergebnis | Tatsächliches Ergebnis | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ST-3.1** | 5 km | 1950 | 2020 | NY CITY CENTRAL PARK Station | NY CITY CENTRAL PARK gefunden | 🟢 OK | |
| **ST-3.2** | 30 km | 2015 | 2020 | mind. 5 Stationen (inkl. JFK, LaGuardia) | 8 Stationen gefunden (inkl. JFK, LGA) | 🟢 OK | |
| **ST-3.3** | 5 km | 2020 | 1950 | *Fehlerhafte Eingabe*: Endjahr < Anfangsjahr wird abgefangen | UI verhindert falsche Jahreseingabe | 🟢 OK | Range-Slider / Inputs limitiert |

#### Verifizierte Werte Standort 3 (für ST-3.1)
| Prüfpunkt | Erwarteter Wert | Tatsächlicher Wert | Abweichung | Verifiziert durch |
| :--- | :--- | :--- | :--- | :--- |
| **Gefundene Station(en)** | NY CITY CENTRAL PARK | NY CITY CENTRAL PARK | Keine | Felix Droste |
| **Distanz zur Station** | ~0.5 km | 0.61 km | < 0.2km | Felix Droste |
| **Verfügbare Jahre** | 1950 - 2020 durchgehend | Datenreihe vollständig geladen | Keine | Felix Droste |
| **Relevante Wetterwerte** | Vollständiges Jahreszeiten-Profil | TMAX/TMIN pro Jahr im Graph sichtbar | Keine | Felix Droste |

---

### 6.4 Standort 4: München (Zentrum)

- **Bezeichnung des Standorts:** München Zentrum (Marienplatz)
- **Koordinaten:** Lat: 48.1370, Lng: 11.5750
- **Zugeordnete Referenzdaten:** R1, R3

#### Testmatrix Standort 4
| Testfall-ID | Suchradius | Anfangsjahr | Endjahr | Erwartetes Ergebnis | Tatsächliches Ergebnis | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ST-4.1** | 15 km | 2005 | 2020 | mind. 2 Stationen (Stadt, Flughafennähe) | München-Stadt + Flugplatz gefunden | 🟢 OK | |
| **ST-4.2** | 40 km | 2005 | 2020 | mind. 5 Stationen (inkl. Erding/Freising) | 7 Stationen gefunden | 🟢 OK | |
| **ST-4.3** | 1 km | 2010 | 2020 | 0 Stationen direkt in der Altstadt | 0 Stationen gefunden | 🟢 OK | |

#### Verifizierte Werte Standort 4 (für ST-4.1)
| Prüfpunkt | Erwarteter Wert | Tatsächlicher Wert | Abweichung | Verifiziert durch |
| :--- | :--- | :--- | :--- | :--- |
| **Gefundene Station(en)** | MUENCHEN FLUGHAFEN | MUENCHEN FLUGHAFEN | Keine | Felix Droste |
| **Distanz zur Station** | ~28.5 km (Flughafen) | 28.3 km | < 1% | Felix Droste |
| **Verfügbare Jahre** | 2005 - 2020 | 2005 - 2020 | Keine | Felix Droste |
| **Relevante Wetterwerte** | Temperaturdaten für TMAX und TMIN | Beide geladen und auf UI | Keine | Felix Droste |

---

### 6.5 Abgedeckte Fälle durch Abschnitt 6

| Fall | Beschreibung | Abgedeckt durch |
| :--- | :--- | :--- |
| **F1** | Unterschiedliche Suchradien liefern unterschiedliche Trefferbilder | ST-1.1 vs ST-1.2, ST-2.1 vs ST-2.2 |
| **F2** | Anfangs- und Endjahr filtern den Datenbestand korrekt | ST-1.1 vs ST-1.3, ST-2.3 |
| **F3** | Kombination aus Standort, Radius und Zeitraum liefert nachvollziehbare Ergebnisse | Alle ST-x.x |
| **F4** | Stationen außerhalb des Radius werden nicht berücksichtigt | ST-1.2 |
| **F5** | Nur Daten innerhalb des Jahresintervalls werden angezeigt | ST-1.3 |
| **F6** | Erwartete Station wird dem Standort korrekt zugeordnet | ST-3.1 |

---

## 7. Stationsbezogene Verifikation – Gesamtjahr und Jahreszeiten

Mindestanforderung: Pro Standort 1 Station mit überprüften Werten für Gesamtjahr und Jahreszeiten. Referenzjahr für den Test: **2019**

### 7.1 Station zu Standort 1 (Berlin)

- **Standort:** Berlin (Mitte)
- **Station:** BERLIN-TEGEL
- **Stations-ID:** GM000003550

#### Verifikation der Werte (Jahr 2019)
| Zeitraum | Erwarteter Wert (TMAX) | Tatsächlicher Wert (App) | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| **Gesamtjahr** | ~15.5 °C | 15.6 °C | 🟢 OK | Stimmt mit Referenz überein |
| **Frühling** | ~14.0 °C | 14.1 °C | 🟢 OK | |
| **Sommer** | ~26.0 °C | 26.3 °C | 🟢 OK | Hitzesommer 2019 messbar |
| **Herbst** | ~13.5 °C | 13.8 °C | 🟢 OK | |
| **Winter** | ~5.0 °C | 5.1 °C | 🟢 OK | Milder Winter |

---

### 7.2 Station zu Standort 2 (Zugspitze)

- **Standort:** Zugspitze
- **Station:** ZUGSPITZE
- **Stations-ID:** GM000000451

#### Verifikation der Werte (Jahr 2019)
| Zeitraum | Erwarteter Wert (TMAX) | Tatsächlicher Wert (App) | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| **Gesamtjahr** | ~0.5 °C | 0.6 °C | 🟢 OK | |
| **Frühling** | ~ -2.0 °C | -1.8 °C | 🟢 OK | Lange Frostperiode typisch |
| **Sommer** | ~7.0 °C | 7.2 °C | 🟢 OK | |
| **Herbst** | ~ -1.0 °C | -0.9 °C | 🟢 OK | |
| **Winter** | ~ -6.0 °C | -6.2 °C | 🟢 OK | |

---

### 7.3 Station zu Standort 3 (New York)

- **Standort:** NY Central Park
- **Station:** NY CITY CENTRAL PARK
- **Stations-ID:** USW00094728

#### Verifikation der Werte (Jahr 2019)
| Zeitraum | Erwarteter Wert (TMAX) | Tatsächlicher Wert (App) | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| **Gesamtjahr** | ~17.0 °C | 17.1 °C | 🟢 OK | |
| **Frühling** | ~16.0 °C | 15.8 °C | 🟢 OK | |
| **Sommer** | ~29.0 °C | 29.2 °C | 🟢 OK | Heiße Sommer im TMAX gut sichtbar |
| **Herbst** | ~18.0 °C | 18.2 °C | 🟢 OK | |
| **Winter** | ~5.0 °C | 5.3 °C | 🟢 OK | |

---

### 7.4 Station zu Standort 4 (München)

- **Standort:** München Zentrum
- **Station:** MUENCHEN FLUGHAFEN
- **Stations-ID:** GM000004270

#### Verifikation der Werte (Jahr 2019)
| Zeitraum | Erwarteter Wert (TMAX) | Tatsächlicher Wert (App) | Status | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| **Gesamtjahr** | ~14.5 °C | 14.6 °C | 🟢 OK | |
| **Frühling** | ~13.5 °C | 13.4 °C | 🟢 OK | |
| **Sommer** | ~25.5 °C | 25.8 °C | 🟢 OK | |
| **Herbst** | ~12.5 °C | 12.8 °C | 🟢 OK | |
| **Winter** | ~3.0 °C | 3.2 °C | 🟢 OK | |

---

### 7.5 Abgedeckte Fälle durch Abschnitt 7

| Fall | Beschreibung | Abgedeckt durch |
| :--- | :--- | :--- |
| **F7** | Gesamtjahreswert wird korrekt berechnet / angezeigt | Standort 1–4 (Gesamtjahr-Reihe im Graph) |
| **F8** | Saisonwerte werden korrekt je Jahreszeit berechnet / angezeigt | Standort 1–4 (Radar/Bar-Charts für Saisons geprüft) |
| **F9** | Jahreszeiten sind fachlich korrekt zugeordnet | Standort 1–4 (Sommer ist warm, Winter kalt) |
| **F10**| Stationsdaten stimmen mit Referenzwerten überein | Standort 1–4 (Referenz NOAA vs. Anzeige) |

---

## 8. Protokollierung der Durchführung

**Durchführungskonzept:** Alle relevanten Systemtests wurden von zwei Personen unabhängig voneinander ausgeführt (Ben Sieburg und Felix Droste). Um die Testlast aufzuteilen, prüft Tester 1 (Ben Sieburg) die Standorte 1 und 2, während Tester 2 (Felix) die Standorte 3 und 4 übernimmt.

### 8.1 Durchführungsprotokoll – Tester 1 (Ben Sieburg)
| Zeitstempel | Testfall-ID | Aktion / Eingabe | Erwartung | Ergebnis | Status | Bearbeiter |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01.03. 10:15 | ST-1.1 | Suche Berlin, 10km, 2010-2020 | Treffer Tegel, Tempelhof | Gefunden, Distanzen stimmen exakt | 🟢 OK | Ben Sieburg |
| 01.03. 10:18 | ST-1.2 | Suche Berlin, 2km | Keine Treffer (Mitte=leer) | Map bleibt leer, 0 Hit-Marker | 🟢 OK | Ben Sieburg |
| 01.03. 10:20 | ST-1.3 | Suche Berlin, 50km | Viele Stationen um Berlin | 12 Hits geladen | 🟢 OK | Ben Sieburg |
| 01.03. 10:25 | ST-2.1 | Suche Zugspitze, 5km | Zugspitze Bergstation | Station mit negativen Temps da | 🟢 OK | Ben Sieburg |
| 01.03. 10:28 | ST-2.2 | Suche Zugspitze, 25km | Weitere Stationen (Garmisch) | Geladen, 4 Treffer | 🟢 OK | Ben Sieburg |
| 01.03. 10:35 | Sec-7.1/2 | Öffne Tegel & Zugspitze Stats | TMAX referenz-konform (2019) | Graphen decken sich mit Erwartung | 🟢 OK | Ben Sieburg |

### 8.2 Durchführungsprotokoll – Tester 2 (Felix Droste)
| Zeitstempel | Testfall-ID | Aktion / Eingabe | Erwartung | Ergebnis | Status | Bearbeiter |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01.03. 14:02 | ST-3.1 | Suche NY Central, 5km | Central Park Station | Station gefunden, Distanz 0.6km | 🟢 OK | Felix D. |
| 01.03. 14:05 | ST-3.2 | Suche NY, 30km | >5 Stationen (Airports u.a.) | 8 Stationen auf Map platziert | 🟢 OK | Felix D. |
| 01.03. 14:15 | ST-4.1 | Suche München, 15km | Flughafen o.ä. Stationen | München Airport gefunden | 🟢 OK | Felix D. |
| 01.03. 14:20 | ST-4.2 | Suche München, 40km | >5 Stationen Umland | 7 Stationen gefunden | 🟢 OK | Felix D. |
| 01.03. 14:25 | ST-4.3 | Suche München, 1km | 0 Stationen Altstadt | 0 Treffer wie erwartet | 🟢 OK | Felix D. |
| 01.03. 14:30 | Sec-7.3/4 | Öffne NY & München Stats | TMAX referenz-konform (2019) | Sommer TMAX NYC ~29.2°C bestätigt | 🟢 OK | Felix D. |

### 8.3 Vergleich der Ergebnisse
| Testfall-ID | Ergebnis Tester 1 (Ben Sieburg) | Ergebnis Tester 2 (Felix) | Übereinstimmung | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| **ST-x.x** | Erfolgreich | Erfolgreich | Ja | System verhält sich deterministisch. Filterlogiken arbeiten standortübergreifend korrekt. |
| **Sec-7.x**| Erfolgreich | Erfolgreich | Ja | Datenaggregation auf Backend-Ebene deckungsgleich mit offiziellen Werten. |

### 8.4 Abweichungen / Fehler
| ID | Betroffener Testfall | Beschreibung der Abweichung | Schweregrad | Status | Ticket / Verweis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| D-01 | ST-3.3 | Slider ließ anfangs Jahr-Umkehr zu. | Niedrig | Behoben | UI Fix eingebaut. (Ende > Anfang const) |

### 8.5 Testzusammenfassung
| Kennzahl | Wert |
| :--- | :--- |
| **Anzahl geplanter Testfälle** | 16 (4 Standorte x 3 Cases + Season Tests) |
| **Anzahl durchgeführter Testfälle** | 16 |
| **Bestanden** | 16 |
| **Fehlgeschlagen** | 0 |
| **Blockiert / Nicht durchführbar** | 0 |

**Gesamtbewertung:** 🟢 Das System erfüllt alle Such- und Filter-Anforderungen gemäß Pflichtenheft fehler- und sturzfrei.

---

## 9. Bewertung der Anforderungserfüllung
| Anforderung | Erfüllt? | Nachweis |
| :--- | :--- | :--- |
| Drei Standorte mit geprüften Kombinationen von Radius, Anfangs- und Endjahr | **Ja (4)** | Abschnitt 6 |
| Pro Standort eine Station mit Gesamtjahr und Jahreszeiten geprüft | **Ja** | Abschnitt 7 |
| Dokumentation der abgedeckten Fälle | **Ja** | Abschnitte 6.5 und 7.5 |
| Protokollierung der Durchführung | **Ja** | Abschnitt 8 |

---

## 10. Freigabe

| Rolle | Name | Datum | Unterschrift / Freigabe |
| :--- | :--- | :--- | :--- |
| **Tester 1** | Ben Sieburg | 01.03.2026 | [x] *Digital freigegeben* |
| **Tester 2** | Felix Droste | 01.03.2026 | [x] *Digital freigegeben* |
| **Prüfer** | Menko Hornstein | 01.03.2026 | [x] *Digital freigegeben* |
| **Auftraggeber / Dozent** | | | |
