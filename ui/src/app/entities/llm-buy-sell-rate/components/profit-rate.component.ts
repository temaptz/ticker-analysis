import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';
import { ProfitRateResp } from '../../../shared/types';
import { GRAPH_COLORS } from '../../../shared/const';

@Component({
  selector: 'profit-rate',
  imports: [CommonModule, MatTooltip],
  providers: [DecimalPipe],
  template: `
    <div class="rate-cell">
      @if (rateData.value(); as data) {
        <div class="profit-percent">
          @if (data.debug?.['potential_profit_percent'] != null) {
            <span [style.color]="data.debug?.['potential_profit_percent'] >= 0 ? '#4caf50' : '#f44336'">
              {{ data.debug?.['potential_profit_percent'] >= 0 ? '+' : '' }}{{ data.debug?.['potential_profit_percent'] | number:'1.2-2' }}%
            </span>
          }
        </div>
        <div
          class="rate-value"
          [style.color]="profitColor"
          [matTooltip]="getTooltip(data)"
          matTooltipClass="rate-tooltip"
        >
          {{ data.rate | number:'1.2-2' }}
        </div>
        <div class="rate-label" [style.color]="profitColor">profit</div>
      } @else if (rateData.isLoading()) {
        <div class="profit-percent">&nbsp;</div>
        <div class="rate-value" [style.color]="profitColor">...</div>
        <div class="rate-label" [style.color]="profitColor">profit</div>
      } @else {
        <div class="profit-percent">&nbsp;</div>
        <div class="rate-value" [style.color]="profitColor">-</div>
        <div class="rate-label" [style.color]="profitColor">profit</div>
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

    .rate-label {
      font-size: 0.75em;
      opacity: 0.7;
    }

    .profit-percent {
      height: 50px;
      display: flex;
      align-items: center;
      font-size: 14px;
      font-weight: 500;
    }

    .rate-value {
      margin-top: 3px;
      font-size: 24px;
      font-weight: 500;
      cursor: help;
    }
  `]
})
export class ProfitRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  profitColor = GRAPH_COLORS.profit_rate;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentProfitRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: ProfitRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
