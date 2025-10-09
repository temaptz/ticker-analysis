import { computed, inject, Injectable, resource, signal } from '@angular/core';
import { BehaviorSubject, firstValueFrom, Observable, switchMap, tap } from 'rxjs';
import { ApiService } from './api.service';
import { CurrentUser } from '../types';
import { toSignal } from '@angular/core/rxjs-interop';


@Injectable({
  providedIn: 'root'
})
export class AuthService {

  token = signal<string | null>(null);

  private _api = inject(ApiService);

  private _refreshUser$ = new BehaviorSubject<unknown>(null);
  private _currentUser$ = this._refreshUser$.pipe(
    switchMap(() => this._api.getCurrentUser()),
  );

  constructor() {
    const storedToken = this.getStoredToken();

    if (storedToken) {
      this.token.set(storedToken);
    }
  }

  login(login: string, password: string): Observable<CurrentUser> {
    return this._api.login(login, password)
      .pipe(
        tap((user: CurrentUser) => {
          if (user) {
            this._refreshUser$.next(user);
            this.storeToken(user.token);
          }
        })
      );
  }

  getCurrentUser(): Observable<CurrentUser> {
    return this._currentUser$;
  }

  private storeToken(token: string): void {
    localStorage.setItem('ticker-analysis.token', token);
    this.token.set(token);
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('ticker-analysis.token') ?? null;
  }

}
