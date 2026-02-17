import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GRAPH_COLORS } from '../../../shared/const';

@Component({
  selector: 'fundamental-rate',
  imports: [CommonModule],
  template: `
    <div class="rate-cell">
      <div class="rate-value" [style.color]="fundamentalColor">0</div>
      <div class="rate-label" [style.color]="fundamentalColor">fundamental</div>
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
      font-size: 1.1em;
      font-weight: 500;
    }
  `]
})
export class FundamentalRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  fundamentalColor = GRAPH_COLORS.ta_3_fundamental;
}
