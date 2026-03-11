import { Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { MapViewComponent } from '../map-view/map-view';
import { SettingsConfiguration } from '../settings-configuration/settings-configuration';
import { PopUpDisplayComponent } from '../pop-up-display/pop-up-display';
import { StationUiStateService } from '../map-view/map-station';

/**
 * Main layout component coordinating the map visualization, search form, 
 * and details popup display. Provides the `StationUiStateService` context.
 */
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

  constructor(public ui: StationUiStateService) { }

  ngOnInit(): void {
    // Other initialization if needed in the future
  }

  /**
   * Handles changes to the dialog visibility state.
   * Ensures the UI state is updated when the dialog is closed externally.
   * 
   * @param v - The new visibility state.
   */
  onDialogVisibleChange(v: boolean): void {
    if (!v) this.ui.closeDialog();
  }
}
