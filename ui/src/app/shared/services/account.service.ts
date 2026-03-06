import { Injectable, signal, computed, inject, resource } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class AccountService {
  private api = inject(ApiService);

  private readonly lsKey = 'selectedAccountId';

  selectedAccountId = signal<number | null>(this.loadAccountId());

  accounts = resource({
    loader: () => firstValueFrom(this.api.getAccounts()),
  });

  userMoneyRub = resource({
    request: () => ({ accountId: this.selectedAccountId() }),
    loader: ({ request }) => {
      if (!request.accountId) return Promise.resolve(0);
      return firstValueFrom(this.api.getUserMoneyRub(request.accountId));
    },
  });

  setSelectedAccount(accountId: number | null): void {
    this.selectedAccountId.set(accountId);
    this.saveAccountId(accountId);
  }

  private loadAccountId(): number | null {
    try {
      const stored = localStorage.getItem(this.lsKey);
      if (stored) return JSON.parse(stored);
    } catch (e) {
      console.error('ERROR loadAccountId', e);
    }
    return null;
  }

  private saveAccountId(accountId: number | null): void {
    try {
      localStorage.setItem(this.lsKey, JSON.stringify(accountId));
    } catch (e) {
      console.error('ERROR saveAccountId', e);
    }
  }
}
