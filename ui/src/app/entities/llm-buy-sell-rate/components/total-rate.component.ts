import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom, map } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';
import { BuySellTotalRateResp } from '../../../shared/types';

@Component({
  selector: 'total-rate',
  imports: [CommonModule, MatTooltip],
  providers: [DecimalPipe],
  template: `
    <div class="rate-cell">
      @if (rateData.value(); as data) {
        <div
          class="rate-value"
          [matTooltip]="getTooltip(data)"
          matTooltipClass="rate-tooltip"
        >
          {{ data.rate | number:'1.2-2' }}
        </div>
        <div class="rate-label">итого</div>
      } @else if (rateData.isLoading()) {
        <div class="rate-value">...</div>
        <div class="rate-label">итого</div>
      } @else {
        <div class="rate-value">-</div>
        <div class="rate-label">итого</div>
      }
    </div>
  `,
  styles: [`
    .rate-cell {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }
    .rate-value {
      font-size: 60px;
      font-weight: 500;
      cursor: help;
    }
    .rate-label {
      margin-top: 20px;
      font-size: 0.75em;
      opacity: 0.7;
    }
  `]
})
export class TotalRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  rateData = resource<BuySellTotalRateResp, { uid: string, isBuy: boolean }>({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string, isBuy: boolean }>) => firstValueFrom(
      this.apiService.getBuySellTotalRate(
        params.request.uid,
        params.request.isBuy
      )
    )
  });

  getTooltip(data: BuySellTotalRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
