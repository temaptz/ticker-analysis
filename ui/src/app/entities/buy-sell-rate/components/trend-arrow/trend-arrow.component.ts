import { Component, computed, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { GRAPH_COLORS } from '../../../../shared/const';


@Component({
  selector: 'trend-arrow',
  imports: [CommonModule],
  providers: [DecimalPipe],
  template: `
    <div>
      @if (isPredictionUpper()) {
        <span [style.color]="GRAPH_COLORS.buy">&nearr;</span>
      } @else if (isPredictionLower()) {
        <span [style.color]="GRAPH_COLORS.sell">&searr;</span>
      } @else if (isPredictionSame()) {
        <span>&rarrc;</span>
      }
    </div>
  `,
  styles: [`
    div {
      height: 50px;
      display: flex;
      align-items: center;
      font-size: 48px;
      font-weight: 600;
      color: gray;
    }
  `]
})
export class TrendArrowComponent {
  prediction = input<string | null>(null);

  protected readonly GRAPH_COLORS = GRAPH_COLORS;

  isPredictionUpper = computed<boolean>(() => this.prediction() === 'upper');
  isPredictionLower = computed<boolean>(() => this.prediction() === 'lower');
  isPredictionSame = computed<boolean>(() => this.prediction() === 'same');
}
