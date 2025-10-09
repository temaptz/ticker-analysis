import { ApplicationConfig, LOCALE_ID, provideZoneChangeDetection } from '@angular/core';
import { registerLocaleData } from '@angular/common';
import { provideHttpClient, withInterceptors, withInterceptorsFromDi } from '@angular/common/http';
import localeRu from '@angular/common/locales/ru';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { authInterceptor } from './shared/interceptors/auth.interceptor';

registerLocaleData(localeRu)

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(
      withInterceptorsFromDi(),
      withInterceptors([authInterceptor])
    ),
    { provide: LOCALE_ID, useValue: 'ru' },
  ]
};
