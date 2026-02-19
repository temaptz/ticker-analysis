import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';
import { VolumeRateResp } from '../../../shared/types';
import { GRAPH_COLORS } from '../../../shared/const';

@Component({
  selector: 'volume-rate',
  imports: [CommonModule, MatTooltip],
  providers: [DecimalPipe],
  template: `
    <div class="rate-cell">
      @if (rateData.value(); as data) {
        <div
          class="rate-value"
          [style.color]="volumeColor"
          [matTooltip]="getTooltip(data)"
          matTooltipClass="rate-tooltip"
        >
          {{ data.rate | number:'1.2-2' }}
        </div>
        <div class="rate-label" [style.color]="volumeColor">volume</div>
      } @else if (rateData.isLoading()) {
        <div class="rate-value" [style.color]="volumeColor">...</div>
        <div class="rate-label" [style.color]="volumeColor">volume</div>
      } @else {
        <div class="rate-value" [style.color]="volumeColor">-</div>
        <div class="rate-label" [style.color]="volumeColor">volume</div>
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
export class VolumeRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  volumeColor = GRAPH_COLORS.volume_rate;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentVolumeRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: VolumeRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
