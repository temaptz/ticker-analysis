import { Injectable, signal, inject, effect } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { BuySellWeights } from '../types';

@Injectable({
  providedIn: 'root'
})
export class WeightsService {
  private readonly _api = inject(ApiService);
  private readonly _auth = inject(AuthService);

  private _buyWeights = signal<BuySellWeights | null>(null);
  private _sellWeights = signal<BuySellWeights | null>(null);

  buyWeights = this._buyWeights.asReadonly();
  sellWeights = this._sellWeights.asReadonly();

  constructor() {
    effect(() => {
      const token = this._auth.token();
      if (token) {
        this.loadWeights();
      }
    });
  }

  async loadWeights(): Promise<void> {
    if (!this._auth.token()) return;
    
    try {
      const [buy, sell] = await Promise.all([
        firstValueFrom(this._api.getBuySellWeights(true)),
        firstValueFrom(this._api.getBuySellWeights(false)),
      ]);
      this._buyWeights.set(buy);
      this._sellWeights.set(sell);
    } catch (e) {
      console.warn('Failed to load weights:', e);
    }
  }

  getWeight(isBuy: boolean, key: keyof BuySellWeights): number {
    const weights = isBuy ? this._buyWeights() : this._sellWeights();
    if (!weights) return 0;
    return (weights[key] ?? 0) * 100;
  }
}
