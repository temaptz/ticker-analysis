import { Component, computed, inject, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { BacktestRateItem } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';
import { WeightsService } from '../../../../shared/services/weights.service';
import { TrendArrowComponent } from '../trend-arrow/trend-arrow.component';

@Component({
  selector: 'backtest-volume',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent, WeightIndicatorComponent, TrendArrowComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        @if (rateData(); as data) {
          <div class="value">
            <trend-arrow [prediction]="data.volume?.debug?.['prediction']"/>
          </div>
          <div
            class="rate-value"
            [style.color]="color"
            [matTooltip]="getTooltip(data)"
            matTooltipClass="rate-tooltip"
          >
            {{ data.volume?.rate ?? 0 | number:'1.2-2' }}
          </div>
          <div class="rate-label" [style.color]="color">volume</div>
          <weight-indicator [weight]="weight()"/>
        } @else {
          <div class="rate-value" [style.color]="color">-</div>
          <div class="rate-label" [style.color]="color">volume</div>
          <weight-indicator [weight]="weight()"/>
        }
      </div>
      <vertical-scale [color]="color" [value]="rateData()?.volume?.rate ?? 0"/>
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
    .value {
      height: 50px;
      display: flex;
      align-items: center;
      font-size: 48px;
      font-weight: 600;
      color: gray;
    }
  `]
})
export class BacktestVolumeComponent {
  readonly rateData = input<BacktestRateItem | null>(null);
  readonly isBuy = input.required<boolean>();

  private weightsService = inject(WeightsService);

  color = GRAPH_COLORS.volume_rate;
  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'volume'));

  getTooltip(data: BacktestRateItem): string {
    return data.volume ? JSON.stringify(data.volume, null, 2) : 'Volume: -';
  }

  prediction = computed<string>(() => (this.rateData()?.volume?.debug as any)?.['prediction']);

  isPredictionUpper = computed<boolean>(() => this.prediction() === 'upper');
  isPredictionLower = computed<boolean>(() => this.prediction() === 'lower');
  isPredictionSame = computed<boolean>(() => this.prediction() === 'same');

  protected readonly GRAPH_COLORS = GRAPH_COLORS;
}
