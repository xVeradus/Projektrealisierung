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
    // Start blocking loading immediately
    this.loading.show();
    this.loading.setMessage("Initialisiere Datenbank... Bitte warten. Dieser Vorgang kann einige Minuten dauern.");

    this.pollBackendReady();
  }

  private pollBackendReady() {
    this.api.ready().subscribe({
      next: (res) => {
        if (res.ready) {
          // Backend is ready!
          this.loading.hide();
          this.loading.setMessage(null);
        } else if (res.error) {
          // Backend reported an initialization error
          this.loading.hide();
          this.loading.setError('Fehler beim Initialisieren: ' + res.error);
        } else {
          // Backend is busy initializing
          // Keep loading screen up, maybe update message if info is available
          if (res.info && res.info.stations_count) {
            this.loading.setMessage(`Initialisiere Datenbank... (${res.info.stations_count} Stationen geladen)`);
          }
          // Retry in 3 seconds
          setTimeout(() => this.pollBackendReady(), 3000);
        }
      },
      error: (err) => {
        console.error('Backend connection check failed:', err);
        // If 503, it might just be starting up (though usually 503 is handled by catching it in service or here)
        // If it's a hard error (connection refused), show error.
        this.loading.hide(); // Hide the "spinner" count so error card shows up if we set error
        this.loading.setError('Das Backend ist nicht erreichbar. Bitte starte den Server.');
      }
    });
  }
}
