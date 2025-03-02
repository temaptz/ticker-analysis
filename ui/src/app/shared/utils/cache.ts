import { Observable, of } from 'rxjs';
import { tap, shareReplay } from 'rxjs/operators';

export function CacheObservable() {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;
    const cache = new Map<string, any>();

    descriptor.value = function (...args: any[]) {
      const cacheKey = JSON.stringify(args);

      if (cache.has(cacheKey)) {
        return of(cache.get(cacheKey));
      }

      console.log('Cache', cacheKey);

      const result$: Observable<any> = originalMethod.apply(this, args).pipe(
        tap(value => cache.set(cacheKey, value)),
        shareReplay(1)
      );

      return result$;
    };

    return descriptor;
  };
}
