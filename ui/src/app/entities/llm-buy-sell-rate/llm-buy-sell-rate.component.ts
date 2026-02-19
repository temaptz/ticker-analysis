import { Component, computed, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VolumeRateComponent } from './components/volume-rate/volume-rate.component';
import { MacdRateComponent } from './components/macd-rate/macd-rate.component';
import { RsiRateComponent } from './components/rsi-rate/rsi-rate.component';
import { TechRateComponent } from './components/tech-rate/tech-rate.component';
import { NewsRateComponent } from './components/news-rate/news-rate.component';
import { FundamentalRateComponent } from './components/fundamental-rate/fundamental-rate.component';
import { ProfitRateComponent } from './components/profit-rate/profit-rate.component';
import { TotalRateComponent } from './components/total-rate/total-rate.component';
import { SortModeService } from '../../shared/services/sort-mode.service';
import { SortModeEnum } from '../../shared/types';


@Component({
  selector: 'llm-buy-sell-rate',
  imports: [
    CommonModule,
    VolumeRateComponent,
    MacdRateComponent,
    RsiRateComponent,
    TechRateComponent,
    NewsRateComponent,
    FundamentalRateComponent,
    ProfitRateComponent,
    TotalRateComponent
  ],
  templateUrl: './llm-buy-sell-rate.component.html',
  styleUrl: './llm-buy-sell-rate.component.scss'
})
export class LlmBuySellRateComponent {
  instrumentUid = input.required<string>();

  private _sortModeService = inject(SortModeService);

  showBuyRow = computed<boolean>(() => {
    const mode = this._sortModeService.sortMode();
    return mode === SortModeEnum.BuyPerspective || 
           mode === SortModeEnum.LastOperation || 
           mode === SortModeEnum.MarketValue;
  });

  showSellRow = computed<boolean>(() => {
    const mode = this._sortModeService.sortMode();
    return mode === SortModeEnum.SellPerspective || 
           mode === SortModeEnum.LastOperation || 
           mode === SortModeEnum.MarketValue;
  });
}
