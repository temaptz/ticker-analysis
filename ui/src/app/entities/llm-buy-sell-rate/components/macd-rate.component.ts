import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';
import { MacdRateResp } from '../../../shared/types';
import { MacdMiniGraphComponent } from './macd/macd-mini-graph.component';

@Component({
  selector: 'macd-rate',
  imports: [CommonModule, MatTooltip, MacdMiniGraphComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-cell">
      <macd-mini-graph [instrumentUid]="instrumentUid()"/>
      @if (rateData.value(); as data) {
        <div
          class="rate-value"
          [matTooltip]="getTooltip(data)"
          matTooltipClass="rate-tooltip"
        >
          {{ (data.rate / 100) | number:'1.2-2' }}
        </div>
        <div class="rate-label">macd</div>
      } @else if (rateData.isLoading()) {
        <div class="rate-value">...</div>
        <div class="rate-label">macd</div>
      } @else {
        <div class="rate-value">-</div>
        <div class="rate-label">macd</div>
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

    .rate-value {
      margin-top: 3px;
      font-size: 24px;
      font-weight: 500;
      cursor: help;
    }
  `]
})
export class MacdRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentMacdRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: MacdRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
