import { Component, DestroyRef, inject, effect, ViewEncapsulation } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormGroup, FormsModule } from '@angular/forms';
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
  imports: [CommonModule, InputNumberModule, DatePickerModule, ButtonModule, ReactiveFormsModule, FormsModule, SliderModule, ToggleSwitchModule, TooltipModule],
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
      year_range: this.fb.control<number[]>([1950, 2025]),
      start_year: this.fb.control<number>(1950),
      end_year: this.fb.control<number>(2025),
    });

    // Sync Slider -> Inputs
    this.form.get('year_range')?.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((range: number[]) => {
        if (range && range.length === 2) {
          this.form.patchValue({
            start_year: range[0],
            end_year: range[1]
          }, { emitEvent: false });
        }
      });

    // Sync Inputs -> Slider
    const syncSliderFromInputs = () => {
      const start = this.form.get('start_year')?.value;
      const end = this.form.get('end_year')?.value;
      if (start !== null && end !== null) {
        // Ensure valid range
        let newStart = start;
        let newEnd = end;
        if (newStart > newEnd) {
          // If start is greater, we don't force fix immediately to allow typing, 
          // but slider might look weird. 
          // Better to let slider clamp or just update. 
          // Let's just update, slider handles it or we fix it.
          // Actually, let's keep it simple.
        }
        this.form.patchValue({ year_range: [newStart, newEnd] }, { emitEvent: false });
      }
    };

    this.form.get('start_year')?.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(syncSliderFromInputs);

    this.form.get('end_year')?.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(syncSliderFromInputs);

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

    // Sync year range to UI state for popups
    if (!v.show_all && v.year_range) {
      this.ui.setYearRange([v.year_range[0], v.year_range[1]]);
    } else {
      this.ui.setYearRange(null);
    }

    const req: StationSearchRequest = {
      lat: v.lat,
      lon: v.lon,
      radius_km: v.radius_km,
      limit: v.show_all ? 1000 : (v.limit ?? 25),
      start_year: (!v.show_all && v.year_range) ? v.year_range[0] : undefined,
      end_year: (!v.show_all && v.year_range) ? v.year_range[1] : undefined,
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
      year_range: [1950, 2025],
      start_year: 1950,
      end_year: 2025,
    });

    this.stations = [];
    this.ui.clear();
    this.ui.setCenter(48.0636, 8.4597, 100);
  }
}
