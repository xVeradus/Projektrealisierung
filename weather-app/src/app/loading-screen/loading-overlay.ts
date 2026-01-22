import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { map } from 'rxjs/operators';
import { LoadingService } from '../loading-screen/loading-screen'
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-loading-overlay',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  template: `
    <div class="overlay" *ngIf="showOverlay$ | async" role="status" aria-live="polite">
      <div class="card" [class.error-card]="errorMessage()" [attr.role]="errorMessage() ? 'alert' : null">
        <ng-container *ngIf="!errorMessage()">
          <div class="spinner" aria-hidden="true"></div>
          <div class="text">Lade Daten…</div>
        </ng-container>

        <ng-container *ngIf="errorMessage()">
          <span class="pi pi-times-circle" style="color: #ef4444; font-size: 1.5rem;" aria-hidden="true"></span>
          <div class="error-container">
            <div class="text text-error">{{ errorMessage() }}</div>
            <p-button label="Erneut versuchen" icon="pi pi-refresh" [outlined]="true" severity="secondary" size="small" (click)="onRetry()" ariaLabel="Ladevorgang erneut versuchen"></p-button>
          </div>
        </ng-container>
      </div>
    </div>
  `,
  styleUrls: ['./loading-screen.css'],
})
export class LoadingOverlayComponent {
  private loading = inject(LoadingService);

  errorMessage = this.loading.errorMessage;

  showOverlay$ = this.loading.isLoading$.pipe(
    map(count => count > 0 || this.errorMessage() !== null)
  );

  onRetry() {
    window.location.reload();
  }
}
