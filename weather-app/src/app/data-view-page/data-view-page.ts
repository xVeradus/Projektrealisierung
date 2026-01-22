import { Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { MapViewComponent } from '../map-view/map-view';
import { SettingsConfiguration } from '../settings-configuration/settings-configuration';
import { PopUpDisplayComponent } from '../pop-up-display/pop-up-display';
import { StationUiStateService } from '../map-view/map-station';

@Component({
  selector: 'app-data-view-page',
  standalone: true,
  imports: [
    CommonModule,
    MapViewComponent,
    SettingsConfiguration,
    PopUpDisplayComponent,
  ],
  templateUrl: './data-view-page.html',
  styleUrl: './data-view-page.css',
  providers: [StationUiStateService],
})
export class DataViewPageComponent implements OnInit {
  private destroyRef = inject(DestroyRef);
  private http = inject(HttpClient);

  private quotes: string[] = [];
  public currentQuote = signal('');

  constructor(public ui: StationUiStateService) { }

  ngOnInit(): void {
    this.http.get<any>('quotes.json').subscribe({
      next: (data) => {
        if (data && data.categories) {
          const categories = Object.values(data.categories);
          this.quotes = categories.reduce((acc: string[], val: any) => acc.concat(val), []);
          this.rotateQuote();
        } else {
          console.warn('Quotes JSON loaded but structure is unexpected:', data);
        }
      },
      error: (err) => console.error('Failed to load quotes.json:', err)
    });

    const interval = setInterval(() => this.rotateQuote(), 10000);

    this.destroyRef.onDestroy(() => {
      clearInterval(interval);
    });
  }

  private rotateQuote(): void {
    if (this.quotes.length === 0) return;

    let next: string;
    do {
      next = this.quotes[Math.floor(Math.random() * this.quotes.length)];
    } while (next === this.currentQuote() && this.quotes.length > 1);

    this.currentQuote.set(next);
  }

  onDialogVisibleChange(v: boolean): void {
    if (!v) this.ui.closeDialog();
  }
}
