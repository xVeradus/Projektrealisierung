import { Injectable, signal } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LoadingService {
  private readonly _count = new BehaviorSubject<number>(0);
  readonly isLoading$ = this._count.asObservable();

  readonly errorMessage = signal<string | null>(null);

  show(): void {
    this._count.next(this._count.value + 1);
  }

  hide(): void {
    this._count.next(Math.max(0, this._count.value - 1));
  }

  setError(msg: string | null): void {
    this.errorMessage.set(msg);
  }

  clearError(): void {
    this.errorMessage.set(null);
  }
}
