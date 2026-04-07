import { Component, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { BacktestRateItem } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';

@Component({
  selector: 'backtest-total',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        @if (rateData(); as data) {
          <div
            class="rate-value"
            [style.color]="color"
            [matTooltip]="getTooltip(data)"
            matTooltipClass="rate-tooltip"
          >
            {{ data.rate | number:'1.2-2' }}
          </div>
          <div class="rate-label" [style.color]="color">итого</div>
        } @else {
          <div class="rate-value" [style.color]="color">-</div>
          <div class="rate-label" [style.color]="color">итого</div>
        }
      </div>
      <vertical-scale [color]="color" [value]="rateData()?.rate ?? 0"/>
    </div>
  `,
  styles: [`
    .rate-wrapper {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
    }
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
export class BacktestTotalComponent {
  readonly rateData = input<BacktestRateItem | null>(null);
  readonly isBuy = input.required<boolean>();
  color = GRAPH_COLORS.total_rate;
  getTooltip(data: BacktestRateItem): string {
    const components = {
      macd: data.macd?.rate ?? 0,
      rsi: data.rsi?.rate ?? 0,
      tech: data.tech?.rate ?? 0,
      news: data.news?.rate ?? 0,
      fundamental: data.fundamental?.rate ?? 0,
      volume: data.volume?.rate ?? 0,
      profit: data.profit?.rate ?? 0
    };
    return `Total: ${data.rate}\n\nComponents:\n${JSON.stringify(components, null, 2)}`;
  }
}
