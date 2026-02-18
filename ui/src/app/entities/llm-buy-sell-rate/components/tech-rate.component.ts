import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';
import { TechRateResp } from '../../../shared/types';
import { GRAPH_COLORS } from '../../../shared/const';
import { TechMiniGraphComponent } from './tech/tech-mini-graph.component';

@Component({
  selector: 'tech-rate',
  imports: [CommonModule, MatTooltip, TechMiniGraphComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-cell">
      <tech-mini-graph [instrumentUid]="instrumentUid()"/>
      @if (rateData.value(); as data) {
        <div
          class="rate-value"
          [style.color]="techColor"
          [matTooltip]="getTooltip(data)"
          matTooltipClass="rate-tooltip"
        >
          {{ (data.rate / 100) | number:'1.2-2' }}
        </div>
        <div class="rate-label" [style.color]="techColor">tech</div>
      } @else if (rateData.isLoading()) {
        <div class="rate-value" [style.color]="techColor">...</div>
        <div class="rate-label" [style.color]="techColor">tech</div>
      } @else {
        <div class="rate-value" [style.color]="techColor">-</div>
        <div class="rate-label" [style.color]="techColor">tech</div>
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
export class TechRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  techColor = GRAPH_COLORS.ta_3_tech;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) => 
      firstValueFrom(this.apiService.getInstrumentTechRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: TechRateResp): string {
    const parts: string[] = [];
    
    parts.push(`rate: ${data.rate / 100}`);
    
    if (data.max_prediction_date !== undefined) {
      parts.push(`max_prediction_date: ${data.max_prediction_date}`);
    }
    if (data.max_prediction_value !== undefined) {
      parts.push(`max_prediction_value: ${data.max_prediction_value}`);
    }
    if (data.days_before_positive !== undefined) {
      parts.push(`days_before_positive: ${data.days_before_positive}`);
    }
    
    const predictionsStr = data.predictions
      .map(v => v !== null ? v : 'null')
      .join(', ');
    parts.push(`predictions: [${predictionsStr}]`);
    
    return parts.join('\n');
  }
}
