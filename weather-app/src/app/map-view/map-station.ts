import { Injectable, signal } from '@angular/core';
import { StationItem } from '../weather-api.service';

export type YearRange = { start?: number; end?: number };

/**
 * Global UI state management service using Angular Signals.
 * Stores the map constraints, loaded stations list, and popup dialog visibility.
 */
@Injectable({ providedIn: 'root' })
export class StationUiStateService {
  /** The coordinate center and radius selected by the user. */
  readonly center = signal<{ lat: number; lon: number; radius_km?: number } | null>(null);

  /** The active list of stations found in the current search radius. */
  readonly stations = signal<StationItem[]>([]);

  /** The ID of the currently selected and inspected weather station. */
  readonly selectedStationId = signal<string | null>(null);

  /** Controls the visibility state of the detail data dialog. */
  readonly dialogVisible = signal<boolean>(false);

  /** The bounding years currently applied to the station search. */
  readonly yearRange = signal<[number, number] | null>(null);

  /**
   * Updates the global search center point and radius.
   */
  setCenter(lat: number, lon: number, radius_km?: number): void {
    this.center.set({ lat, lon, radius_km });
  }

  setYearRange(range: [number, number] | null): void {
    this.yearRange.set(range);
  }

  setStations(stations: StationItem[]): void {
    this.stations.set(stations);
  }

  /**
   * Opens the detail dialog for the specified station ID.
   */
  openStation(stationId: string): void {
    this.selectedStationId.set(stationId);
    this.dialogVisible.set(true);
  }

  /**
   * Hides the detail dialog window.
   */
  closeDialog(): void {
    this.dialogVisible.set(false);
  }

  /**
   * Retrieves the readable name of a station from the loaded cache by its ID.
   */
  getStationName(id: string): string | null {
    const s = this.stations().find((st) => st.station_id === id);
    return s ? s.name : null;
  }

  /**
   * Resets all UI states back to their default (empty) values.
   */
  clear(): void {
    this.stations.set([]);
    this.selectedStationId.set(null);
    this.dialogVisible.set(false);
    this.center.set(null);
  }
}
