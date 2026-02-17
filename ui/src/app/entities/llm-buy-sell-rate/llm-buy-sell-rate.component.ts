import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VolumeRateComponent } from './components/volume-rate.component';
import { MacdRateComponent } from './components/macd-rate.component';
import { RsiRateComponent } from './components/rsi-rate.component';
import { TechRateComponent } from './components/tech-rate.component';
import { FundamentalRateComponent } from './components/fundamental-rate.component';
import { TotalRateComponent } from './components/total-rate.component';


@Component({
  selector: 'llm-buy-sell-rate',
  imports: [
    CommonModule,
    VolumeRateComponent,
    MacdRateComponent,
    RsiRateComponent,
    TechRateComponent,
    FundamentalRateComponent,
    TotalRateComponent
  ],
  templateUrl: './llm-buy-sell-rate.component.html',
  styleUrl: './llm-buy-sell-rate.component.scss'
})
export class LlmBuySellRateComponent {
  instrumentUid = input.required<string>();
}
