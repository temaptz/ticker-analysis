import { Component, computed, effect, inject, resource, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { MatSortModule } from '@angular/material/sort';
import { firstValueFrom, of } from 'rxjs';
import { TableVirtualScrollDataSource, TableVirtualScrollModule } from 'ng-table-virtual-scroll';
import { ApiService } from '../../shared/services/api.service';
import { SortModeService } from '../../shared/services/sort-mode.service';
import { AccountService } from '../../shared/services/account.service';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { CurrentPriceByUidPipe } from '../../shared/pipes/current-price-by-uid.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { InstrumentInList, SortModeEnum } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { BuySellRateComponent } from '../../entities/buy-sell-rate/buy-sell-rate.component';
import { DrawerComponent } from '../../entities/drawer/drawer.component';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { InstrumentOrdersComponent } from '../../entities/instrument-orders/instrument-orders.component';


@Component({
  selector: 'table-full',
  imports: [
    CommonModule,
    MatTableModule,
    ScrollingModule,
    InstrumentLogoComponent,
    BalanceComponent,
    ComplexGraphComponent,
    MatSortModule,
    RouterModule,
    TableVirtualScrollModule,
    CurrentPriceByUidPipe,
    PriceFormatPipe,
    BuySellRateComponent,
    DrawerComponent,
    PreloaderComponent,
    InstrumentOrdersComponent,
  ],
  providers: [],
  templateUrl: './table-full.component.html',
  styleUrl: './table-full.component.scss'
})
export class TableFullComponent {
  isLoaded = signal<boolean>(false);
  dataSource = new TableVirtualScrollDataSource<InstrumentInList>([])

  private _sortModeService = inject(SortModeService);
  public accountService = inject(AccountService);
  private _apiService = inject(ApiService);

  sortTickers = this._sortModeService.sortMode;

  instrumentsResource = resource<InstrumentInList[], {accountId: number | null, sort: number | null}>({
    defaultValue: [],
    params: () => ({
      accountId: this.accountService.selectedAccountId() ?? null,
      sort: this._sortModeService.sortMode() ?? null,
    }),
    loader: ({params, abortSignal}) => {
      if (!params?.accountId || !params?.sort) {
        return firstValueFrom(of([]));
      }
      return firstValueFrom(this._apiService.getInstruments(params.accountId, params.sort));
    },
  });

  ratingColumnTitle = computed<string>(() => {
    if (this.isShowBuy()) {
      return 'Рейтинг покупки';
    } else if (this.isShowSell()) {
      return 'Рейтинг продажи';
    } else {
      return 'Рейтинг покупки и продажи';
    }
  });

  isShowBuy = computed<boolean>(() => [
    SortModeEnum.BuyVolume,
    SortModeEnum.BuyMacd,
    SortModeEnum.BuyRsi,
    SortModeEnum.BuyTech,
    SortModeEnum.BuyFundamental,
    SortModeEnum.BuyPerspective,
    SortModeEnum.BuyProfit,
    SortModeEnum.BuyNews,
    SortModeEnum.BuyTotalRate,
  ].includes(this.sortTickers()));

  isShowSell = computed<boolean>(() => [
    SortModeEnum.SellVolume,
    SortModeEnum.SellMacd,
    SortModeEnum.SellRsi,
    SortModeEnum.SellTech,
    SortModeEnum.SellFundamental,
    SortModeEnum.SellPerspective,
    SortModeEnum.SellProfit,
    SortModeEnum.SellNews,
    SortModeEnum.SellTotalRate,
  ].includes(this.sortTickers()));

  protected readonly CandleInterval = CandleInterval;
  protected readonly tableItemHeightPx = 350;

  displayedColumns: string[] = [
    'logo',
    'complex',
    'buy_sell_rate',
    'balance',
    'instrument_orders',
  ];

  constructor() {
    effect(() => {
      const instruments = this.instrumentsResource.value();
      const isLoading = this.instrumentsResource.isLoading();
      this.dataSource.data = (isLoading ? [] : instruments) ?? [];
    });
  }

}
