import { Injectable, signal } from '@angular/core';
import { StationItem } from '../weather-api.service';

export type YearRange = { start?: number; end?: number };

@Injectable({ providedIn: 'root' })
export class StationUiStateService {
  readonly center = signal<{ lat: number; lon: number; radius_km?: number } | null>(null);
  readonly stations = signal<StationItem[]>([]);
  readonly selectedStationId = signal<string | null>(null);
  readonly dialogVisible = signal<boolean>(false);

  setCenter(lat: number, lon: number, radius_km?: number): void {
    this.center.set({ lat, lon, radius_km });
  }

  setStations(stations: StationItem[]): void {
    this.stations.set(stations);
  }

  openStation(stationId: string): void {
    this.selectedStationId.set(stationId);
    this.dialogVisible.set(true);
  }

  closeDialog(): void {
    this.dialogVisible.set(false);
  }

  getStationName(id: string): string | null {
    const s = this.stations().find((st) => st.station_id === id);
    return s ? s.name : null;
  }

  clear(): void {
    this.stations.set([]);
    this.selectedStationId.set(null);
    this.dialogVisible.set(false);
    this.center.set(null);
  }
}
