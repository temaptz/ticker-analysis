import { Component, computed, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { BacktestRateItem } from '../../../../shared/types';
import { VerticalScaleComponent } from '../../../../shared/components/vertical-scale/vertical-scale.component';

@Component({
  selector: 'backtest-base-rate',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent],
  template: `
    <div class="rate-wrapper">
      <div class="rate-cell">
        @if (rateData(); as data) {
          <div 
            class="rate-value" 
            [style.color]="color()"
            [matTooltip]="tooltip()"
            matTooltipClass="rate-tooltip"
          >
            {{ data.rate | number:'1.2-2' }}
          </div>
          <div class="rate-label" [style.color]="color()">{{ label() }}</div>
        } @else {
          <div class="rate-value" [style.color]="color()">-</div>
          <div class="rate-label" [style.color]="color()">{{ label() }}</div>
        }
      </div>
      <vertical-scale [color]="color()" [value]="rateData()?.rate ?? 0"/>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
    
    .rate-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 60px;
    }
    
    .rate-cell {
      text-align: center;
      padding: 8px 4px;
    }
    
    .rate-value {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 2px;
    }
    
    .rate-label {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
  `]
})
export class BacktestBaseRateComponent {
  rateData = input<BacktestRateItem | null>(null);
  label = input.required<string>();
  color = input.required<string>();
  debugKey = input.required<string>();
  
  tooltip = computed(() => {
    const data = this.rateData();
    if (!data) return '';
    const value = data.debug?.[this.debugKey()];
    return value !== undefined ? `${this.label()}: ${value}` : '';
  });
}
