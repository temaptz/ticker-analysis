import { Component, computed, effect, inject, resource, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { MatSortModule } from '@angular/material/sort';
import { firstValueFrom } from 'rxjs';
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
import { LlmBuySellRateComponent } from '../../entities/llm-buy-sell-rate/llm-buy-sell-rate.component';
import { DrawerComponent } from '../../entities/drawer/drawer.component';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { InstrumentOrdersComponent } from '../../entities/instrument-orders/instrument-orders.component';


@Component({
  selector: 'table-full-3',
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
    LlmBuySellRateComponent,
    DrawerComponent,
    PreloaderComponent,
    InstrumentOrdersComponent,
  ],
  providers: [],
  templateUrl: './table-full-3.component.html',
  styleUrl: './table-full-3.component.scss'
})
export class TableFull3Component {
  isLoaded = signal<boolean>(false);
  dataSource = new TableVirtualScrollDataSource<InstrumentInList>([])

  private _sortModeService = inject(SortModeService);
  private _accountService = inject(AccountService);
  private _apiService = inject(ApiService);

  sortTickers = this._sortModeService.sortMode;
  selectedAccountId = this._accountService.selectedAccountId;

  instrumentsResource = resource({
    request: () => ({
      sort: this.sortTickers(),
      accountId: this.selectedAccountId(),
    }),
    loader: ({ request }) => {
      if (!request.accountId) {
        return Promise.resolve([]);
      }
      return firstValueFrom(this._apiService.getInstruments(request.sort, request.accountId));
    },
  });

  ratingColumnTitle = computed<string>(() => {
    const mode = this.sortTickers();
    if (mode === SortModeEnum.BuyPerspective) {
      return 'Рейтинг покупки';
    } else if (mode === SortModeEnum.SellPerspective) {
      return 'Рейтинг продажи';
    } else {
      return 'Рейтинг покупки и продажи';
    }
  });

  protected readonly CandleInterval = CandleInterval;
  protected readonly tableItemHeightPx = 350;
  protected readonly tableMinBufferPx = 350 * 2;
  protected readonly tableMaxBufferPx = 350 * 3;

  displayedColumns: string[] = [
    'logo',
    'complex',
    'balance',
    'llm_buy_sell_rate',
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
