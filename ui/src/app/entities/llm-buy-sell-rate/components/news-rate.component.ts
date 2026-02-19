import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';
import { NewsRateResp } from '../../../shared/types';
import { GRAPH_COLORS } from '../../../shared/const';
import { NewsMiniGraphComponent } from './news/news-mini-graph.component';

@Component({
  selector: 'news-rate',
  imports: [CommonModule, MatTooltip, NewsMiniGraphComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-cell">
      <news-mini-graph [instrumentUid]="instrumentUid()"/>
      @if (rateData.value(); as data) {
        <div
          class="rate-value"
          [style.color]="newsColor"
          [matTooltip]="getTooltip(data)"
          matTooltipClass="rate-tooltip"
        >
          {{ data.rate | number:'1.2-2' }}
        </div>
        <div class="rate-label" [style.color]="newsColor">news</div>
      } @else if (rateData.isLoading()) {
        <div class="rate-value" [style.color]="newsColor">...</div>
        <div class="rate-label" [style.color]="newsColor">news</div>
      } @else {
        <div class="rate-value" [style.color]="newsColor">-</div>
        <div class="rate-label" [style.color]="newsColor">news</div>
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
export class NewsRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  newsColor = GRAPH_COLORS.news_influence_score;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentNewsRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: NewsRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
