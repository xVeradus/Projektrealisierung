import { Injectable } from '@angular/core';
import { HttpInterceptorFn } from '@angular/common/http';
import { finalize } from 'rxjs/operators';
import { inject } from '@angular/core';
import { LoadingService } from './loading-screen';

/**
 * HTTP Interceptor that globally triggers the loading screen for pending requests.
 * Allows bypassing the loading screen by passing the `X-Skip-Loading` header.
 */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  const loading = inject(LoadingService);

  if (req.headers.has('X-Skip-Loading')) {
    const newReq = req.clone({ headers: req.headers.delete('X-Skip-Loading') });
    return next(newReq);
  }

  loading.show();
  return next(req).pipe(finalize(() => loading.hide()));
};
