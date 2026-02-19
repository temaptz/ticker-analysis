import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';
import { FundamentalRateResp } from '../../../shared/types';
import { GRAPH_COLORS } from '../../../shared/const';

@Component({
  selector: 'fundamental-rate',
  imports: [CommonModule, MatTooltip],
  providers: [DecimalPipe],
  template: `
    <div class="rate-cell">
      @if (rateData.value(); as data) {
        <div
          class="rate-value"
          [style.color]="fundamentalColor"
          [matTooltip]="getTooltip(data)"
          matTooltipClass="rate-tooltip"
        >
          {{ data.rate | number:'1.2-2' }}
        </div>
        <div class="rate-label" [style.color]="fundamentalColor">fundamental</div>
      } @else if (rateData.isLoading()) {
        <div class="rate-value" [style.color]="fundamentalColor">...</div>
        <div class="rate-label" [style.color]="fundamentalColor">fundamental</div>
      } @else {
        <div class="rate-value" [style.color]="fundamentalColor">-</div>
        <div class="rate-label" [style.color]="fundamentalColor">fundamental</div>
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
export class FundamentalRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  fundamentalColor = GRAPH_COLORS.ta_3_fundamental;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentFundamentalRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: FundamentalRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
