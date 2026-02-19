import { Component, computed, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VolumeComponent } from './components/volume/volume.component';
import { MacdComponent } from './components/macd/macd.component';
import { RsiComponent } from './components/rsi/rsi.component';
import { TechComponent } from './components/tech/tech.component';
import { NewsComponent } from './components/news/news.component';
import { FundamentalComponent } from './components/fundamental/fundamental.component';
import { ProfitComponent } from './components/profit/profit.component';
import { TotalComponent } from './components/total/total.component';
import { SortModeService } from '../../shared/services/sort-mode.service';
import { SortModeEnum } from '../../shared/types';


@Component({
  selector: 'llm-buy-sell-rate',
  imports: [
    CommonModule,
    VolumeComponent,
    MacdComponent,
    RsiComponent,
    TechComponent,
    NewsComponent,
    FundamentalComponent,
    ProfitComponent,
    TotalComponent
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
           mode === SortModeEnum.MarketValue ||
           mode === SortModeEnum.BuyVolume ||
           mode === SortModeEnum.BuyMacd ||
           mode === SortModeEnum.BuyRsi ||
           mode === SortModeEnum.BuyTech ||
           mode === SortModeEnum.BuyNews ||
           mode === SortModeEnum.BuyFundamental ||
           mode === SortModeEnum.BuyProfit ||
           mode === SortModeEnum.BuyTotalRate;
  });

  showSellRow = computed<boolean>(() => {
    const mode = this._sortModeService.sortMode();
    return mode === SortModeEnum.SellPerspective ||
           mode === SortModeEnum.LastOperation ||
           mode === SortModeEnum.MarketValue ||
           mode === SortModeEnum.SellVolume ||
           mode === SortModeEnum.SellMacd ||
           mode === SortModeEnum.SellRsi ||
           mode === SortModeEnum.SellTech ||
           mode === SortModeEnum.SellNews ||
           mode === SortModeEnum.SellFundamental ||
           mode === SortModeEnum.SellProfit ||
           mode === SortModeEnum.SellTotalRate;
  });
}
