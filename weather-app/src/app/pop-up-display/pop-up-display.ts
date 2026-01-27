import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges, inject, DestroyRef, ViewEncapsulation, ViewChild, ChangeDetectorRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { DialogModule } from 'primeng/dialog';
import { ChartModule, UIChart } from 'primeng/chart';
import { SelectModule } from 'primeng/select';
import { FormsModule } from '@angular/forms';
import { SliderModule } from 'primeng/slider';
import { InputNumberModule } from 'primeng/inputnumber';
import { CheckboxModule } from 'primeng/checkbox';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TableModule } from 'primeng/table';
import { ToggleButtonModule } from 'primeng/togglebutton';
import { Subscription } from 'rxjs';

import { WeatherApiService, TempRow, Period } from '../weather-api.service';
import { StationUiStateService } from '../map-view/map-station';

@Component({
  selector: 'pop-up-display',
  standalone: true,
  imports: [CommonModule, DialogModule, ChartModule, SelectModule, FormsModule, SliderModule, InputNumberModule, CheckboxModule, ProgressSpinnerModule, TableModule, ToggleButtonModule],
  templateUrl: './pop-up-display.html',
  styleUrl: './pop-up-display.css',
  encapsulation: ViewEncapsulation.None,
})
export class PopUpDisplayComponent implements OnChanges {
  @Input() visible = false;
  @Output() visibleChange = new EventEmitter<boolean>();

  @ViewChild('chart') chart: UIChart | undefined;

  @Input() initialRange: [number, number] | null = null;
  @Input() stationId: string | null = null;
  stationName: string | null = null;

  private cdr = inject(ChangeDetectorRef);
  private ui = inject(StationUiStateService);
  private destroyRef = inject(DestroyRef);
  private loadSubscription?: Subscription;

  currentRange: { start: number; end: number } = { start: 1980, end: 2025 };
  minYear = 1900;
  maxYear = 2025;
  selectedRange: [number, number] = [1980, 2025];
  showTmax = true;
  showTmin = true;
  loading = false;
  hasVisibleData = false;
  error: string | null = null;
  isTableView = false;

  selectedPeriods: Period[] = ['annual']; // Changed from single period
  periodOptions: { label: string; value: Period }[] = [
    { label: 'Annual', value: 'annual' },
    { label: 'Winter', value: 'winter' },
    { label: 'Spring', value: 'spring' },
    { label: 'Summer', value: 'summer' },
    { label: 'Autumn', value: 'autumn' },
  ];

  /* 
   * Color mapping for multi-period display
   * Tmax is stronger, Tmin is lighter or complementary
   */
  periodColors: Record<Period, { tmax: string; tmin: string }> = {
    annual: { tmax: '#ef4444', tmin: '#3b82f6' }, // Red / Blue
    spring: { tmax: '#16a34a', tmin: '#86efac' }, // Green / Light Green
    summer: { tmax: '#f97316', tmin: '#fbbf24' }, // Orange / Amber
    autumn: { tmax: '#78350f', tmin: '#d6d3d1' }, // Brown / Light Grey
    winter: { tmax: '#0ea5e9', tmin: '#a855f7' }, // Cyan / Purple
  };

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
        // dash: [4, 4]
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
        // ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.restore();
      }
    }
  };

  constructor(private api: WeatherApiService) { }

  ngOnChanges(changes: SimpleChanges): void {
    const relevant = changes['stationId'];

    if (this.visible && relevant) {
      // If we have an initial range from settings, apply it
      if (this.initialRange) {
        this.currentRange = { start: this.initialRange[0], end: this.initialRange[1] };
        this.selectedRange = [...this.initialRange];
      }

      this.load();
    }
  }

  onVisibleChange(v: boolean): void {
    this.visible = v;
    this.visibleChange.emit(v);
  }

  onShow(): void {
    // 1. Ensure chart is resized correctly after Dialog animation (approx 300ms)
    this.forceChartRefresh();

    // 2. Only load if we haven't already
    if (!this.rowsCache.length) {
      this.load();
    }
  }

  private forceChartRefresh(): void {
    setTimeout(() => {
      this.cdr.detectChanges();
      this.chart?.refresh();
      window.dispatchEvent(new Event('resize'));
    }, 350);
  }

  togglePeriod(p: Period): void {
    if (this.selectedPeriods.includes(p)) {
      // Prevent deselecting the last one to avoid empty state? Or allow it?
      // Let's allow it but maybe defaults to annual if empty? User might want to clear all.
      // Actually simpler: just toggle.
      this.selectedPeriods = this.selectedPeriods.filter(x => x !== p);
    } else {
      this.selectedPeriods.push(p);
    }

    // Sort logic to keep legend consistent: annual -> winter -> spring -> summer -> autumn
    const order = ['annual', 'winter', 'spring', 'summer', 'autumn'];
    this.selectedPeriods.sort((a, b) => order.indexOf(a) - order.indexOf(b));

    // Re-calculate range for the new period selection!
    this.recalcRangeForPeriod();
    this.chartData = this.buildChart(this.rowsCache);
  }

  onRangeChange(): void {
    this.currentRange = { start: this.selectedRange[0], end: this.selectedRange[1] };
    this.chartData = this.buildChart(this.rowsCache);
  }

  onInputYearChange(): void {
    this.selectedRange = [this.currentRange.start, this.currentRange.end];
    this.chartData = this.buildChart(this.rowsCache);
  }

  onToggleDataset(): void {
    this.chartData = this.buildChart(this.rowsCache);
  }

  private recalcRangeForPeriod(): void {
    if (!this.rowsCache.length) return;

    // If initial range is fixed (from settings), DO NOT auto-adjust minYear/maxYear based on data content
    // However, the user might want to see the limits of the data. 
    // The previous logic was: find min/max of VALID data.

    // Union of all selected periods
    const validYears = this.rowsCache
      .filter(r => this.selectedPeriods.includes(r.period) && this.isValidRow(r, r.period))
      .map(r => r.year);

    if (validYears.length > 0) {
      this.minYear = Math.min(...validYears);
      this.maxYear = Math.max(...validYears);
    } else {
      // Fallback
      this.minYear = 1900;
      this.maxYear = new Date().getFullYear();
    }

    // If we have an initial range, we might want to respect it, but we also need to respect data limits.
    // For now, let's keep the slider limits based on data, but the selected handles based on user choice.

    // Only reset handles if they are outside valid range OR if this is a fresh load (handled in ngOnChanges/load)
    // Actually, if user toggles period, let's keep the range as is unless it's null.

    // Safe check
    if (this.currentRange.start < this.minYear) this.currentRange.start = this.minYear;
    if (this.currentRange.end > this.maxYear) this.currentRange.end = this.maxYear;

    this.selectedRange = [this.currentRange.start, this.currentRange.end];
  }

  load(): void {
    // 1. Cancel previous request if running
    this.loadSubscription?.unsubscribe();

    if (!this.stationId) return;

    this.stationName = this.ui.getStationName(this.stationId);

    this.error = null;
    this.loading = true;

    this.loadSubscription = this.api.getStationTemps(this.stationId).subscribe({
      next: (rows: TempRow[]) => {
        this.loading = false;
        this.rowsCache = rows ?? [];

        // If initial range was provided, don't override it with auto-calc in recalcRangeForPeriod UNLESS necessary.
        // Actually recalcRangeForPeriod sets bounds.
        // Let's modify recalc logic slightly above or just re-apply initial if valid.

        this.recalcRangeForPeriod();

        if (this.initialRange) {
          // Ensure initial range is respected even if recalc tried to snap
          this.currentRange.start = Math.max(this.minYear, this.initialRange[0]);
          this.currentRange.end = Math.min(this.maxYear, this.initialRange[1]);
          this.selectedRange = [this.currentRange.start, this.currentRange.end];
        }

        this.chartData = this.buildChart(this.rowsCache);

        // Force refresh to fix layout glitches
        this.forceChartRefresh();
      },
      error: () => {
        this.loading = false;
        this.error = 'Could not load temperature data.';
      },
    });
  }

  get tableData(): any[] {
    const { start, end } = this.currentRange;
    const yearStart = Math.floor(start);
    const yearEnd = Math.floor(end);

    const data: any[] = [];

    // Flatten data for table: Year | Period | Tmax | Tmin
    // Filtering by selected periods

    const rows = (this.rowsCache ?? []).filter(r =>
      this.selectedPeriods.includes(r.period) &&
      r.year >= yearStart && r.year <= yearEnd
    );

    for (const r of rows) {
      if (this.isValidRow(r, r.period)) {
        data.push({
          year: r.year,
          period: r.period, // Add period column
          tmax: r.avg_tmax_c,
          tmin: r.avg_tmin_c
        });
      }
    }

    // Sort descending by Year, then by Period index
    const periodOrder = ['annual', 'winter', 'spring', 'summer', 'autumn'];
    return data.sort((a, b) => {
      if (b.year !== a.year) return b.year - a.year;
      return periodOrder.indexOf(a.period) - periodOrder.indexOf(b.period);
    });
  }

  private buildChart(rows: TempRow[]) {
    const { start, end } = this.currentRange;
    const yearStart = Math.floor(start);
    const yearEnd = Math.floor(end);

    const datasets: any[] = [];
    const labels: string[] = [];

    // Generate labels once
    for (let y = yearStart; y <= yearEnd; y++) {
      labels.push(String(y));
    }

    let globalHasData = false;

    // Loop through each selected period and create datasets
    this.selectedPeriods.forEach(p => {
      // Create Dictionary for this period
      const rowMap = new Map<number, TempRow>();
      (rows ?? []).forEach((r) => {
        if (r.period === p) rowMap.set(r.year, r);
      });

      const tmaxData: (number | null)[] = [];
      const tminData: (number | null)[] = [];

      for (let y = yearStart; y <= yearEnd; y++) {
        const row = rowMap.get(y);
        const valid = row ? this.isValidRow(row, p) : false;

        if (valid && row) {
          tmaxData.push(row.avg_tmax_c);
          tminData.push(row.avg_tmin_c);
          globalHasData = true;
        } else {
          tmaxData.push(null);
          tminData.push(null);
        }
      }

      const colors = this.periodColors[p];
      const labelPrefix = p.charAt(0).toUpperCase() + p.slice(1); // Capitalize

      datasets.push({
        label: `${labelPrefix} Tmax`,
        data: tmaxData,
        borderColor: colors.tmax,
        backgroundColor: colors.tmax,
        hidden: !this.showTmax,
        tension: 0.3,
        spanGaps: false,
        pointRadius: 3,
        pointHoverRadius: 5,
      });

      datasets.push({
        label: `${labelPrefix} Tmin`,
        data: tminData,
        borderColor: colors.tmin,
        backgroundColor: colors.tmin,
        hidden: !this.showTmin,
        tension: 0.3,
        spanGaps: false,
        pointRadius: 3,
        pointHoverRadius: 5,
      });
    });

    this.hasVisibleData = globalHasData;

    return {
      labels: labels,
      datasets: datasets,
    };
  }

  private isValidRow(row: TempRow, period: Period): boolean {
    // Strict quality check to avoid "outliers" from incomplete years.
    // Annual: require ~10 months (300 days). Seasonal: require ~2.5 months (80 days).
    const minDays = period === 'annual' ? 300 : 80;

    // Check both TMAX and TMIN counts
    return row.n_tmax >= minDays && row.n_tmin >= minDays;
  }
}
