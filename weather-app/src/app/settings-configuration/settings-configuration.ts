import { Component, DestroyRef, inject, effect, ViewEncapsulation, OnInit } from '@angular/core';
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

/**
 * Component providing the main search and configuration form.
 * Directly syncs user input bounding box/limit filters with the UI State Service 
 * and executing searches via the Weather API.
 */
@Component({
  selector: 'app-settings-configuration',
  standalone: true,
  imports: [CommonModule, FormsModule, InputNumberModule, DatePickerModule, ButtonModule, ReactiveFormsModule, SliderModule, ToggleSwitchModule, TooltipModule],
  templateUrl: './settings-configuration.html',
  styleUrl: './settings-configuration.css',
  encapsulation: ViewEncapsulation.None,
})
export class SettingsConfiguration implements OnInit {
  private destroyRef = inject(DestroyRef);

  stations: StationItem[] = [];
  globalMinYear: number = 1900;
  globalMaxYear: number = 2025;

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
      limit: this.fb.control<number>(10, Validators.required),
      show_all: this.fb.control<boolean>(true),
      station_id: this.fb.control<string | null>(null),
      year_range: this.fb.control<number[]>([1950, 2025]),
      start_year: this.fb.control<number>(1950),
      end_year: this.fb.control<number>(2025),
    });

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

    const syncSliderFromInputs = () => {
      const start = this.form.get('start_year')?.value;
      const end = this.form.get('end_year')?.value;
      if (start !== null && end !== null) {
        let newStart = start;
        let newEnd = end;
        if (newStart > newEnd) {
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

  ngOnInit(): void {
    // Trigger initial search after form is initialized.
    setTimeout(() => {
      this.searchStations();
    });
  }

  openStationDialogFor(stationId: string): void {
    this.form.patchValue({ station_id: stationId }, { emitEvent: false });
    this.ui.openStation(stationId);
  }

  trackByStationId(_: number, s: StationItem): string {
    return s.station_id;
  }

  /**
   * Reads the current form values, updates the visual map search constraints, 
   * and dispatches the search request to the backend API.
   */
  searchStations(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.getRawValue() as any;
    this.ui.setCenter(v.lat, v.lon, v.radius_km);

    if (!v.show_all && v.year_range) {
      this.ui.setYearRange([v.year_range[0], v.year_range[1]]);
    } else {
      this.ui.setYearRange(null);
    }

    const req: StationSearchRequest = {
      lat: v.lat,
      lon: v.lon,
      radius_km: v.radius_km,
      limit: v.show_all ? 1000 : (v.limit ?? 10),
      start_year: (!v.show_all && v.year_range) ? v.year_range[0] : undefined,
      end_year: (!v.show_all && v.year_range) ? v.year_range[1] : undefined,
    };

    this.api.searchStations(req).subscribe({
      next: (stations: StationItem[]) => {
        this.stations = stations;
        this.ui.setStations(stations);

        if (stations.length > 0) {
          const mins = stations.map(s => s.start_year).filter(y => y != null) as number[];
          const maxs = stations.map(s => s.end_year).filter(y => y != null) as number[];
          if (mins.length > 0) this.globalMinYear = Math.min(...mins);
          if (maxs.length > 0) this.globalMaxYear = Math.max(...maxs);
          
          const currentRange = this.form.get('year_range')?.value;
          if (currentRange) {
            let [s, e] = currentRange;
            if (s < this.globalMinYear) s = this.globalMinYear;
            if (e > this.globalMaxYear) e = this.globalMaxYear;
            if (s > e) s = e;
            this.form.patchValue({ year_range: [s, e] }, { emitEvent: false });
          }
        }

        const firstId = stations.length ? stations[0].station_id : null;
        this.form.patchValue({ station_id: firstId }, { emitEvent: false });
      },
      error: (err: unknown) => console.error('Error searching stations:', err),
    });
  }

  /**
   * Resets the entire form and mapping visualization back to default values.
   */
  reset(): void {
    this.form.reset({
      lat: 48.0636,
      lon: 8.4597,
      radius_km: 100,
      limit: 10,
      show_all: true,
      station_id: null,
      year_range: [1950, 2025],
      start_year: 1950,
      end_year: 2025,
    });

    this.globalMinYear = 1900;
    this.globalMaxYear = 2025;
    this.stations = [];
    this.ui.clear();
    this.ui.setCenter(48.0636, 8.4597, 100);
  }
}
