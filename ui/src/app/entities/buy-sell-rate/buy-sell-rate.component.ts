import { Component, computed, inject, input, resource } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { BacktestRateResp, BacktestRateItem } from '../../shared/types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { BacktestVolumeComponent } from './components/volume/volume.component';
import { BacktestMacdComponent } from './components/macd/macd.component';
import { BacktestRsiComponent } from './components/rsi/rsi.component';
import { BacktestTechComponent } from './components/tech/tech.component';
import { BacktestNewsComponent } from './components/news/news.component';
import { BacktestFundamentalComponent } from './components/fundamental/fundamental.component';
import { BacktestProfitComponent } from './components/profit/profit.component';
import { BuySellConsensusComponent } from './components/consensus/consensus.component';
import { BacktestTotalComponent } from './components/total/total.component';
import { GRAPH_COLORS } from '../../shared/const';

const EMPTY_BACKTEST_ITEM: BacktestRateItem = {
  rate: 0,
  macd: null,
  rsi: null,
  tech: null,
  news: null,
  fundamental: null,
  volume: null,
  profit: null,
  consensus: null,
};

@Component({
  selector: 'buy-sell-rate',
  imports: [
    CommonModule,
    PreloaderComponent,
    BacktestVolumeComponent,
    BacktestMacdComponent,
    BacktestRsiComponent,
    BacktestTechComponent,
    BacktestNewsComponent,
    BacktestFundamentalComponent,
    BacktestProfitComponent,
    BuySellConsensusComponent,
    BacktestTotalComponent,
  ],
  templateUrl: './buy-sell-rate.component.html',
  styleUrl: './buy-sell-rate.component.scss'
})
export class BuySellRateComponent {
  readonly instrumentUid = input.required<string>();
  readonly accountId = input.required<number>();
  readonly isShowBuy = input<boolean>(true);
  readonly isShowSell = input<boolean>(true);
  readonly selectedDate = input<Date | undefined>(undefined);

  private apiService = inject(ApiService);

  rateData = resource<BacktestRateResp, { uid: string; accountId: number; date: Date | undefined; isBuy: boolean, isSell: boolean }>({
    params: () => ({
      uid: this.instrumentUid(),
      accountId: this.accountId(),
      date: this.selectedDate(),
      isBuy: this.isShowBuy(),
      isSell: this.isShowSell(),
    }),
    loader: (params): Promise<BacktestRateResp> => {
      if (!params?.params?.uid || !params?.params?.accountId) {
        return Promise.resolve({
          total_buy: EMPTY_BACKTEST_ITEM,
          total_sell: EMPTY_BACKTEST_ITEM,
        } as BacktestRateResp);
      }
      return firstValueFrom(
        this.apiService.getRate(
          params.params.uid,
          params.params.accountId,
          params.params.date,
          params.params.isBuy,
          params.params.isSell
        )
      );
    },
  });
  protected readonly GRAPH_COLORS = GRAPH_COLORS;
}
