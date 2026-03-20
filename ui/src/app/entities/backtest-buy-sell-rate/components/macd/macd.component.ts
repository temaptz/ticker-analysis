import { Component, computed, inject, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { BacktestRateItem } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';
import { WeightsService } from '../../../../shared/services/weights.service';
import { BacktestMacdMiniGraphComponent } from '../macd-mini-graph/macd-mini-graph.component';

@Component({
  selector: 'backtest-macd',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent, WeightIndicatorComponent, BacktestMacdMiniGraphComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        <backtest-macd-mini-graph [graphData]="rateData()?.macd?.debug?.['graph']"/>
        @if (rateData(); as data) {
          <div
            class="rate-value"
            [style.color]="color"
            [matTooltip]="getTooltip(data)"
            matTooltipClass="rate-tooltip"
          >
            {{ data.macd?.rate ?? 0 | number:'1.2-2' }}
          </div>
          <div class="rate-label" [style.color]="color">macd</div>
          <weight-indicator [weight]="weight()"/>
        } @else {
          <div class="rate-value" [style.color]="color">-</div>
          <div class="rate-label" [style.color]="color">macd</div>
          <weight-indicator [weight]="weight()"/>
        }
      </div>
      <vertical-scale [color]="color" [value]="rateData()?.macd?.rate ?? 0"/>
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
export class BacktestMacdComponent {
  readonly rateData = input<BacktestRateItem | null>(null);
  readonly isBuy = input.required<boolean>();

  private weightsService = inject(WeightsService);

  color = GRAPH_COLORS.tech_macd;
  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'macd'));

  getTooltip(data: BacktestRateItem): string {
    return data.macd ? JSON.stringify(data.macd, null, 2) : 'MACD: -';
  }
}
