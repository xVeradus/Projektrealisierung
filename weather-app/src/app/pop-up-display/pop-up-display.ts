import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges, inject, DestroyRef, ViewEncapsulation } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { DialogModule } from 'primeng/dialog';
import { ChartModule } from 'primeng/chart';
import { SelectModule } from 'primeng/select';
import { FormsModule } from '@angular/forms';
import { SliderModule } from 'primeng/slider';
import { InputNumberModule } from 'primeng/inputnumber';
import { CheckboxModule } from 'primeng/checkbox';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { WeatherApiService, TempRow, Period } from '../weather-api.service';
import { StationUiStateService } from '../map-view/map-station';

@Component({
  selector: 'pop-up-display',
  standalone: true,
  imports: [CommonModule, DialogModule, ChartModule, SelectModule, FormsModule, SliderModule, InputNumberModule, CheckboxModule, ProgressSpinnerModule],
  templateUrl: './pop-up-display.html',
  styleUrl: './pop-up-display.css',
  encapsulation: ViewEncapsulation.None,
})
export class PopUpDisplayComponent implements OnChanges {
  @Input() visible = false;
  @Output() visibleChange = new EventEmitter<boolean>();

  @Input() stationId: string | null = null;
  stationName: string | null = null;

  private ui = inject(StationUiStateService);
  private destroyRef = inject(DestroyRef);

  currentRange: { start: number; end: number } = { start: 1980, end: 2025 };
  minYear = 1900;
  maxYear = 2025;
  selectedRange: [number, number] = [1980, 2025];
  showTmax = true;
  showTmin = true;
  loading = false;
  error: string | null = null;

  period: Period = 'annual';
  periodOptions = [
    { label: 'Annual', value: 'annual' },
    { label: 'Winter', value: 'winter' },
    { label: 'Spring', value: 'spring' },
    { label: 'Summer', value: 'summer' },
    { label: 'Autumn', value: 'autumn' },
  ];

  rowsCache: TempRow[] = [];

  chartData: any;
  chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(30, 41, 59, 0.9)',
        titleFont: { size: 14, weight: 'bold' },
        bodyFont: { size: 13 },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
      },
      crosshair: {
        color: '#64748b',
        width: 1,
        dash: [4, 4]
      }
    }
  };

  public crosshairPlugin = {
    id: 'crosshair',
    afterDraw: (chart: any) => {
      if (chart.tooltip?._active?.length) {
        const x = chart.tooltip._active[0].element.x;
        const yAxis = chart.scales.y;
        const ctx = chart.ctx;
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(x, yAxis.top);
        ctx.lineTo(x, yAxis.bottom);
        ctx.lineWidth = 1;
        ctx.strokeStyle = '#64748b';
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.restore();
      }
    }
  };

  constructor(private api: WeatherApiService) { }

  ngOnChanges(changes: SimpleChanges): void {
    const relevant = changes['stationId'];

    if (this.visible && relevant) {
      this.load();
    }
  }

  onVisibleChange(v: boolean): void {
    this.visible = v;
    this.visibleChange.emit(v);
  }

  onShow(): void {
    this.load();
  }

  onPeriodChange(): void {
    this.chartData = this.buildChart(this.rowsCache, this.period);
  }

  onRangeChange(): void {
    this.currentRange = { start: this.selectedRange[0], end: this.selectedRange[1] };
    this.chartData = this.buildChart(this.rowsCache, this.period);
  }

  onInputYearChange(): void {
    this.selectedRange = [this.currentRange.start, this.currentRange.end];
    this.chartData = this.buildChart(this.rowsCache, this.period);
  }

  onToggleDataset(): void {
    this.chartData = this.buildChart(this.rowsCache, this.period);
  }

  load(): void {
    if (!this.stationId) return;

    this.stationName = this.ui.getStationName(this.stationId);

    this.error = null;
    this.rowsCache = [];
    this.loading = true;

    this.api.getStationTemps(this.stationId).subscribe({
      next: (rows: TempRow[]) => {
        this.loading = false;
        this.rowsCache = rows ?? [];
        if (this.rowsCache.length > 0) {
          const years = this.rowsCache.map(r => r.year);
          this.minYear = Math.min(...years);
          this.maxYear = Math.max(...years);
          this.currentRange = { start: this.minYear, end: this.maxYear };
          this.selectedRange = [this.minYear, this.maxYear];
        }
        this.chartData = this.buildChart(this.rowsCache, this.period);
      },
      error: () => {
        this.loading = false;
        this.error = 'Could not load temperature data.';
      },
    });
  }

  private buildChart(rows: TempRow[], period: Period) {
    const { start, end } = this.currentRange;
    const filtered = (rows ?? [])
      .filter((r) => r.period === period)
      .filter((r) => {
        if (start !== undefined && r.year < start) return false;
        if (end !== undefined && r.year > end) return false;
        return true;
      })
      .filter((r) =>
        period === 'annual'
          ? (r.n_tmax >= 300 && r.n_tmin >= 300)
          : (r.n_tmax >= 80 && r.n_tmin >= 80)
      )
      .sort((a, b) => a.year - b.year);

    return {
      labels: filtered.map((r) => String(r.year)),
      datasets: [
        {
          label: 'Avg Tmax (°C)',
          data: filtered.map((r) => r.avg_tmax_c),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          hidden: !this.showTmax,
          tension: 0.3
        },
        {
          label: 'Avg Tmin (°C)',
          data: filtered.map((r) => r.avg_tmin_c),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          hidden: !this.showTmin,
          tension: 0.3
        },
      ],
    };
  }
}
