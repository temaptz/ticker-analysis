import { Component, computed, inject, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { BacktestRateItem } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';
import { WeightsService } from '../../../../shared/services/weights.service';
import { BacktestNewsMiniGraphComponent } from '../news-mini-graph/news-mini-graph.component';

@Component({
  selector: 'backtest-news',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent, WeightIndicatorComponent, BacktestNewsMiniGraphComponent],
  providers: [DecimalPipe],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        <backtest-news-mini-graph [graphData]="rateData()?.news?.debug?.['graph']"/>
        @if (rateData(); as data) {
          <div
            class="rate-value"
            [style.color]="color"
            [matTooltip]="getTooltip(data)"
            matTooltipClass="rate-tooltip"
          >
            {{ data.news?.rate ?? 0 | number:'1.2-2' }}
          </div>
          <div class="rate-label" [style.color]="color">news</div>
          <weight-indicator [weight]="weight()"/>
        } @else {
          <div class="rate-value" [style.color]="color">-</div>
          <div class="rate-label" [style.color]="color">news</div>
          <weight-indicator [weight]="weight()"/>
        }
      </div>
      <vertical-scale [color]="color" [value]="rateData()?.news?.rate ?? 0"/>
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
export class BacktestNewsComponent {
  readonly rateData = input<BacktestRateItem | null>(null);
  readonly isBuy = input.required<boolean>();

  private weightsService = inject(WeightsService);

  color = GRAPH_COLORS.news_influence_score;
  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'news'));

  getTooltip(data: BacktestRateItem): string {
    return data.news ? JSON.stringify(data.news, null, 2) : 'News: -';
  }
}
