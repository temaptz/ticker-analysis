import { Component, inject, resource, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { BuySellWeights } from '../../shared/types';


const WEIGHT_LABELS: Record<keyof BuySellWeights, string> = {
  macd: 'MACD',
  rsi: 'RSI',
  tech: 'Тех. анализ',
  news: 'Новости',
  fundamental: 'Фундаментал',
  volume: 'Объём',
  profit: 'Прибыль',
};

type WeightKey = keyof BuySellWeights;


@Component({
  selector: 'weights-editor',
  imports: [CommonModule, FormsModule],
  templateUrl: './weights-editor.component.html',
  styleUrl: './weights-editor.component.scss',
})
export class WeightsEditorComponent {

  private _api = inject(ApiService);

  buyWeights = resource({
    loader: () => firstValueFrom(this._api.getBuySellWeights(true)),
  });

  sellWeights = resource({
    loader: () => firstValueFrom(this._api.getBuySellWeights(false)),
  });

  editBuyWeights = signal<BuySellWeights | null>(null);
  editSellWeights = signal<BuySellWeights | null>(null);

  isBuyDirty = signal<boolean>(false);
  isSellDirty = signal<boolean>(false);

  isSaving = signal<boolean>(false);

  weightKeys: WeightKey[] = ['macd', 'rsi', 'tech', 'news', 'fundamental', 'volume', 'profit'];

  getLabel(key: WeightKey): string {
    return WEIGHT_LABELS[key];
  }

  getEditWeights(isBuy: boolean): BuySellWeights | null {
    if (isBuy) {
      return this.editBuyWeights() ?? this.buyWeights.value() ?? null;
    }
    return this.editSellWeights() ?? this.sellWeights.value() ?? null;
  }

  getWeightValue(isBuy: boolean, key: WeightKey): number {
    const weights = this.getEditWeights(isBuy);
    return weights ? weights[key] : 0;
  }

  getWeightBg(isBuy: boolean, key: WeightKey): string {
    const value = this.getWeightValue(isBuy, key);
    const alpha = Math.min(Math.max(value / 100, 0), 1);
    return `rgba(63, 81, 181, ${alpha.toFixed(2)})`;
  }

  getWeightColor(isBuy: boolean, key: WeightKey): string {
    const value = this.getWeightValue(isBuy, key);
    return value / 100 > 0.45 ? '#fff' : '#333';
  }

  handleWeightChange(isBuy: boolean, key: WeightKey, event: Event): void {
    const value = parseFloat((event.target as HTMLInputElement).value) || 0;
    const current = this.getEditWeights(isBuy);
    const updated = { ...(current ?? { macd: 0, rsi: 0, tech: 0, news: 0, fundamental: 0, volume: 0, profit: 0 }) };
    updated[key] = value;

    if (isBuy) {
      this.editBuyWeights.set(updated);
      this.isBuyDirty.set(true);
    } else {
      this.editSellWeights.set(updated);
      this.isSellDirty.set(true);
    }
  }

  async handleSave(isBuy: boolean): Promise<void> {
    const weights = this.getEditWeights(isBuy);
    if (!weights) return;

    this.isSaving.set(true);
    try {
      await firstValueFrom(this._api.setBuySellWeights(isBuy, weights));
      if (isBuy) {
        this.editBuyWeights.set(null);
        this.isBuyDirty.set(false);
        this.buyWeights.reload();
      } else {
        this.editSellWeights.set(null);
        this.isSellDirty.set(false);
        this.sellWeights.reload();
      }
    } finally {
      this.isSaving.set(false);
    }
  }


}
