import { Component, DestroyRef, inject, effect, ViewEncapsulation } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormGroup } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { InputNumberModule } from 'primeng/inputnumber';
import { DatePickerModule } from 'primeng/datepicker';
import { ButtonModule } from 'primeng/button';
import { SliderModule } from 'primeng/slider';
import { ToggleSwitchModule } from 'primeng/toggleswitch';
import { TooltipModule } from 'primeng/tooltip';
import { debounceTime, distinctUntilChanged } from 'rxjs';

import { StationItem, WeatherApiService, StationSearchRequest } from '../weather-api.service';
import { StationUiStateService } from '../map-view/map-station';

@Component({
  selector: 'app-settings-configuration',
  standalone: true,
  imports: [CommonModule, InputNumberModule, DatePickerModule, ButtonModule, ReactiveFormsModule, SliderModule, ToggleSwitchModule, TooltipModule],
  templateUrl: './settings-configuration.html',
  styleUrl: './settings-configuration.css',
  encapsulation: ViewEncapsulation.None,
})
export class SettingsConfiguration {
  private destroyRef = inject(DestroyRef);

  stations: StationItem[] = [];

  form: FormGroup;

  constructor(
    private fb: FormBuilder,
    private api: WeatherApiService,
    private ui: StationUiStateService
  ) {
    this.form = this.fb.group({
      lat: this.fb.control<number>(48.0636, Validators.required),
      lon: this.fb.control<number>(8.4597, Validators.required),
      radius_km: this.fb.control<number>(100, Validators.required),
      limit: this.fb.control<number>(25, Validators.required),
      show_all: this.fb.control<boolean>(true),
      station_id: this.fb.control<string | null>(null),
    });

    effect(() => {
      const id = this.ui.selectedStationId();
      this.form.patchValue({ station_id: id }, { emitEvent: false });
    });

    effect(() => {
      const center = this.ui.center();
      if (center) {
        const current = this.form.getRawValue();
        const latChanged = Math.abs(current.lat - center.lat) > 0.0001;
        const lonChanged = Math.abs(current.lon - center.lon) > 0.0001;
        const radiusChanged = center.radius_km !== undefined && center.radius_km !== current.radius_km;

        if (latChanged || lonChanged || radiusChanged) {
          this.form.patchValue({
            lat: center.lat,
            lon: center.lon,
            radius_km: center.radius_km ?? current.radius_km
          });
          this.searchStations();
        }
      }
    });

    this.form.valueChanges
      .pipe(
        debounceTime(400),
        distinctUntilChanged((a, b) => JSON.stringify(a) === JSON.stringify(b)),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe(() => {
        this.searchStations();
      });

    this.ui.setCenter(48.0636, 8.4597, 100);
  }

  openStationDialogFor(stationId: string): void {
    this.form.patchValue({ station_id: stationId }, { emitEvent: false });
    this.ui.openStation(stationId);
  }

  trackByStationId(_: number, s: StationItem): string {
    return s.station_id;
  }

  searchStations(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.getRawValue() as any;
    this.ui.setCenter(v.lat, v.lon, v.radius_km);

    const req: StationSearchRequest = {
      lat: v.lat,
      lon: v.lon,
      radius_km: v.radius_km,
      limit: v.show_all ? 1000 : (v.limit ?? 25),
    };

    this.api.searchStations(req).subscribe({
      next: (stations: StationItem[]) => {
        this.stations = stations;
        this.ui.setStations(stations);

        const firstId = stations.length ? stations[0].station_id : null;
        this.form.patchValue({ station_id: firstId }, { emitEvent: false });
      },
      error: (err: unknown) => console.error('Error searching stations:', err),
    });
  }

  reset(): void {
    this.form.reset({
      lat: 48.0636,
      lon: 8.4597,
      radius_km: 100,
      limit: 25,
      show_all: true,
      station_id: null,
    });

    this.stations = [];
    this.ui.clear();
    this.ui.setCenter(48.0636, 8.4597, 100);
  }
}
