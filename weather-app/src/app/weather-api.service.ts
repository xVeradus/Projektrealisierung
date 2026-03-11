import { Injectable } from "@angular/core";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Observable, timeout, catchError } from "rxjs";

/**
 * Structure of the request payload for the nearby stations search.
 */
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
  start_year?: number;
  end_year?: number;
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

/**
 * Service for interacting with the Python FastAPI backend.
 * Provides methods for checking system readiness, searching stations,
 * and fetching temperature aggregation data.
 */
@Injectable({ providedIn: "root" })
export class WeatherApiService {
  private readonly apiUrl = "http://127.0.0.1:8000";

  constructor(private http: HttpClient) { }

  /**
   * Checks if the backend SQLite database is initialized and ready.
   * 
   * @returns An Observable emitting the readiness status and potential error info.
   */
  ready(): Observable<ReadyResponse> {
    return this.http.get<ReadyResponse>(`${this.apiUrl}/api/ready`);
  }

  /**
   * Simple echo test endpoint.
   */
  echo(q: string): Observable<{ echo: string }> {
    return this.http.get<{ echo: string }>(`${this.apiUrl}/api/echo`, {
      params: { q },
    });
  }

  /**
   * Searches for weather stations matching the specified coordinate and radius constraints.
   * 
   * @param req - The configured search parameters.
   * @returns An Observable emitting a list of matching nearby stations.
   */
  searchStations(req: StationSearchRequest): Observable<StationItem[]> {
    return this.http.post<StationItem[]>(`${this.apiUrl}/api/stations/search`, req);
  }

  /**
   * Fetches annual and seasonal temperature data periods for a specific station.
   * Note: Bypasses the global loading screen interceptor.
   * 
   * @param stationId - The 11-character NOAA station identifier.
   * @returns An Observable emitting rows of temperature averages and counts.
   */
  getStationTemps(stationId: string): Observable<TempRow[]> {
    return this.http.get<TempRow[]>(
      `${this.apiUrl}/api/stations/${encodeURIComponent(stationId)}/temps`,
      { headers: { 'X-Skip-Loading': 'true' } }
    );
  }
}
