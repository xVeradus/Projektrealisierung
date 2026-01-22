import { Injectable } from "@angular/core";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Observable, timeout, catchError } from "rxjs";

export interface StationSearchRequest {
  lat: number;
  lon: number;
  radius_km: number;
  limit: number;
  start_year?: number;
  end_year?: number;
}

export interface StationItem {
  station_id: string;
  name: string;
  lat: number;
  lon: number;
  distance_km: number;
}

export interface ReadyResponse {
  ready: boolean;
  error?: string | null;
  info?: any;
}

export interface TempPoint {
  year: number;
  period: string;
  avg_tmax_c: number | null;
  avg_tmin_c: number | null;
  n_tmax: number;
  n_tmin: number;
}

export type Period = 'annual' | 'winter' | 'spring' | 'summer' | 'autumn';

export interface TempRow {
  year: number;
  period: Period;
  avg_tmax_c: number | null;
  avg_tmin_c: number | null;
  n_tmax: number;
  n_tmin: number;
}

@Injectable({ providedIn: "root" })
export class WeatherApiService {
  private readonly apiUrl = "http://127.0.0.1:8000";

  constructor(private http: HttpClient) { }

  ready(): Observable<ReadyResponse> {
    return this.http.get<ReadyResponse>(`${this.apiUrl}/api/ready`);
  }

  echo(q: string): Observable<{ echo: string }> {
    return this.http.get<{ echo: string }>(`${this.apiUrl}/api/echo`, {
      params: { q },
    });
  }

  searchStations(req: StationSearchRequest): Observable<StationItem[]> {
    return this.http.post<StationItem[]>(`${this.apiUrl}/api/stations/search`, req);
  }

  getStationTemps(stationId: string): Observable<TempRow[]> {
    return this.http.get<TempRow[]>(
      `${this.apiUrl}/api/stations/${encodeURIComponent(stationId)}/temps`
    );
  }
}
