import { ApplicationConfig, LOCALE_ID, inject, provideAppInitializer, provideZoneChangeDetection } from '@angular/core';
import { registerLocaleData } from '@angular/common';
import { provideHttpClient, withInterceptors, withInterceptorsFromDi } from '@angular/common/http';
import localeRu from '@angular/common/locales/ru';
import { provideRouter } from '@angular/router';
import { OAuthService, provideOAuthClient } from 'angular-oauth2-oidc';
import { routes } from './app.routes';
import { authInterceptor } from './shared/interceptors/auth.interceptor';
import { authConfig } from './auth.config';
import { of } from 'rxjs';

registerLocaleData(localeRu);

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(
      withInterceptorsFromDi(),
      withInterceptors([authInterceptor])
    ),
    provideOAuthClient(),
    provideAppInitializer(() => {
      if (!window.location.origin.includes('localhost')) {
        const oauthService = inject(OAuthService);
        oauthService.configure(authConfig);
        oauthService.setupAutomaticSilentRefresh();
        return oauthService.loadDiscoveryDocumentAndTryLogin().catch((e) => {
          console.error('Failed to load discovery document', e);
          return of();
        });
      }
      return of();
    }),
    { provide: LOCALE_ID, useValue: 'ru' },
  ],
};
