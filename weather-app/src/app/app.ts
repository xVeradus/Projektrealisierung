import { Component, signal, inject, OnInit } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DataViewPageComponent } from './data-view-page/data-view-page';
import { LoadingOverlayComponent } from './loading-screen/loading-overlay';
import { WeatherApiService } from './weather-api.service';
import { LoadingService } from './loading-screen/loading-screen';

@Component({
  selector: 'app-root',
  imports: [ButtonModule, DataViewPageComponent, LoadingOverlayComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  protected readonly title = signal('angular19-primeng19-tailwind4');

  private api = inject(WeatherApiService);
  private loading = inject(LoadingService);

  ngOnInit() {
    this.checkConnectivity();
  }

  private checkConnectivity() {
    this.loading.clearError();
    this.api.ready().subscribe({
      error: (err) => {
        console.error('Backend connection check failed:', err);
        this.loading.setError('Das Backend ist nicht erreichbar. Bitte starte den Server.');
      }
    });
  }
}
