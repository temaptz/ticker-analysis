import { Component, computed, inject, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { BacktestRateItem } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';
import { WeightsService } from '../../../../shared/services/weights.service';

@Component({
  selector: 'backtest-fundamental',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent, WeightIndicatorComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        @if (rateData(); as data) {
          <div class="value">
            @if (data.fundamental?.debug?.['prediction'] != null) {
              <span [style.color]="data.fundamental?.debug?.['prediction'] >= 0 ? GRAPH_COLORS.buy : GRAPH_COLORS.sell">
                {{ data.fundamental?.debug?.['prediction'] >= 0 ? '+' : '' }}{{ (data.fundamental?.debug?.['prediction'] ?? 0) * 100 | number:'1.4-4' }}%
              </span>
            }
          </div>
          <div
            class="rate-value"
            [style.color]="color"
            [matTooltip]="getTooltip(data)"
            matTooltipClass="rate-tooltip"
          >
            {{ data.fundamental?.rate ?? 0 | number:'1.2-2' }}
          </div>
          <div class="rate-label" [style.color]="color">fundamental</div>
          <weight-indicator [weight]="weight()"/>
        } @else {
          <div class="rate-value" [style.color]="color">-</div>
          <div class="rate-label" [style.color]="color">fundamental</div>
          <weight-indicator [weight]="weight()"/>
        }
      </div>
      <vertical-scale [color]="color" [value]="rateData()?.fundamental?.rate ?? 0"/>
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
      font-size: 14px;
      font-weight: 600;
    }
  `]
})
export class BacktestFundamentalComponent {
  readonly rateData = input<BacktestRateItem | null>(null);
  readonly isBuy = input.required<boolean>();
  
  private weightsService = inject(WeightsService);
  
  color = GRAPH_COLORS.ta_3_fundamental;
  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'fundamental'));
  
  getTooltip(data: BacktestRateItem): string { 
    return data.fundamental ? JSON.stringify(data.fundamental, null, 2) : 'Fundamental: -'; 
  }

  protected readonly GRAPH_COLORS = GRAPH_COLORS;
}
