import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";

@Injectable({ providedIn: 'root' })
export class WeatherApiService {
  private baseUrl = 'http://127.0.0.1:8000';
  apiUrl = this.baseUrl;  

  constructor(private http: HttpClient) {}

  echo(q: string): Observable<{ echo: string }> {
    return this.http.get<{ echo: string }>(`${this.apiUrl}/api/echo`, { params: { q } });
  }
}