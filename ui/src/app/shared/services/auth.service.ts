import { computed, inject, Injectable } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map, startWith, tap } from 'rxjs';
import { OAuthService } from 'angular-oauth2-oidc';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private _lsKey = 'auth_token';
  private _lsToken: string | null = null;

  private _oauthService = inject(OAuthService);

  token = toSignal<string | null>(
    this._oauthService.events.pipe(
      filter(e => e.type === 'token_received' || e.type === 'token_refreshed'),
      map(() => this._oauthService.getAccessToken() ?? null),
      tap(token => this._saveLs(token)),
      startWith(this._getFromLs()),
    ),
    { initialValue: null }
  );

  isAuthenticated = computed<boolean>(() => !!this.token());

  login(): void {
    this._oauthService.initLoginFlow();
  }

  logout(): void {
    this._oauthService.logOut();
    this._saveLs(null);
  }

  getAccessToken(): string | null {
    return this.token() ?? this._getFromLs();
  }

  private _saveLs(token: string | null): void {
    if (token) {
      localStorage.setItem(this._lsKey, token);
    } else {
      localStorage.removeItem(this._lsKey);
    }
  }

  private _getFromLs(): string | null {
    return localStorage.getItem(this._lsKey) ?? null;
  }
}
