import { Component, computed, inject, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { BacktestRateItem } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';
import { WeightsService } from '../../../../shared/services/weights.service';
import { BacktestRsiMiniGraphComponent } from '../rsi-mini-graph/rsi-mini-graph.component';

@Component({
  selector: 'backtest-rsi',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent, WeightIndicatorComponent, BacktestRsiMiniGraphComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        <backtest-rsi-mini-graph [graphData]="rateData()?.rsi?.debug?.['graph']"/>
        @if (rateData(); as data) {
          <div
            class="rate-value"
            [style.color]="color"
            [matTooltip]="getTooltip(data)"
            matTooltipClass="rate-tooltip"
          >
            {{ data.rsi?.rate ?? 0 | number:'1.2-2' }}
          </div>
          <div class="rate-label" [style.color]="color">rsi</div>
          <weight-indicator [weight]="weight()"/>
        } @else {
          <div class="rate-value" [style.color]="color">-</div>
          <div class="rate-label" [style.color]="color">rsi</div>
          <weight-indicator [weight]="weight()"/>
        }
      </div>
      <vertical-scale [color]="color" [value]="rateData()?.rsi?.rate ?? 0"/>
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
export class BacktestRsiComponent {
  readonly rateData = input<BacktestRateItem | null>(null);
  readonly isBuy = input.required<boolean>();

  private weightsService = inject(WeightsService);

  color = GRAPH_COLORS.tech_rsi;
  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'rsi'));

  getTooltip(data: BacktestRateItem): string {
    return data.rsi ? JSON.stringify(data.rsi, null, 2) : 'RSI: -';
  }
}
