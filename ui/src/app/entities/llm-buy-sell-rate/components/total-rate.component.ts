import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../shared/services/api.service';

@Component({
  selector: 'total-rate',
  imports: [CommonModule, MatTooltip],
  template: `
    <div class="rate-cell">
      @if (rate.value(); as rateValue) {
        <div
          class="rate-value"
          [matTooltip]="conclusion.value() || '-'"
          matTooltipClass="rate-tooltip"
        >
          {{ rateValue }}
        </div>
        <div class="rate-label">итого</div>
      } @else if (rate.isLoading()) {
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

  rate = resource<string, string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      this.apiService.getInstrumentTag(
        params.request,
        this.isBuy() ? 'llm_buy_rate' : 'llm_sell_rate'
      )
    )
  });

  conclusion = resource<string, string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      this.apiService.getInstrumentTag(
        params.request,
        this.isBuy() ? 'llm_buy_conclusion' : 'llm_sell_conclusion'
      )
    )
  });
}
