import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';

import { SettingsConfiguration } from '../settings-configuration/settings-configuration';
import { SettingsFilter } from '../settings-filter/settings-filter';
import { SettingsToggle } from '../settings-toggle/settings-toggle';
import { WeatherApiService } from '../weather-api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    SettingsConfiguration,
    SettingsFilter,
    SettingsToggle,
  ],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class Settings {
  result: string = '—';

  constructor(private api: WeatherApiService) {}

  testBackend() {
    this.api.echo('Angular->FastAPI').subscribe({
      next: (res) => {
        this.result = res.echo;
      },
      error: (err) => {
        console.error(err);
        this.result = 'ERROR (siehe Console)';
      },
    });
  }
}
