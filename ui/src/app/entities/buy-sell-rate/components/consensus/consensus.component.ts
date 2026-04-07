import { Component, computed, inject, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { BacktestRateItem } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';
import { WeightsService } from '../../../../shared/services/weights.service';

@Component({
  selector: 'buy-sell-consensus',
  imports: [CommonModule, VerticalScaleComponent, WeightIndicatorComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        <div class="value" [style.color]="color">
          {{ rateData()?.consensus?.rate ?? 0 | number:'1.2-2' }}
        </div>
        <div class="rate-label" [style.color]="color">consensus</div>
        <weight-indicator [weight]="weight()"/>
      </div>
      <vertical-scale [color]="color" [value]="rateData()?.consensus?.rate ?? 0"/>
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
    .value {
      margin-top: 3px;
      font-size: 24px;
      font-weight: 500;
      cursor: help;
    }
  `]
})
export class BuySellConsensusComponent {
  readonly rateData = input<BacktestRateItem | null>(null);
  readonly isBuy = input.required<boolean>();

  private weightsService = inject(WeightsService);

  color = GRAPH_COLORS.consensus_rate;
  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'consensus'));

}
