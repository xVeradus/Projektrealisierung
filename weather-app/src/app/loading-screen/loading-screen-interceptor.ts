import { Injectable } from '@angular/core';
import { HttpInterceptorFn } from '@angular/common/http';
import { finalize } from 'rxjs/operators';
import { inject } from '@angular/core';
import { LoadingService } from './loading-screen';

export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  const loading = inject(LoadingService);

  loading.show();
  return next(req).pipe(finalize(() => loading.hide()));
};
