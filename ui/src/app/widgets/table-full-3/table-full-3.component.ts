import { Component, computed, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { toObservable } from '@angular/core/rxjs-interop';
import { switchMap, tap } from 'rxjs';
import { TableVirtualScrollDataSource, TableVirtualScrollModule } from 'ng-table-virtual-scroll';
import { ApiService } from '../../shared/services/api.service';
import { SortModeService } from '../../shared/services/sort-mode.service';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { CurrentPriceByUidPipe } from '../../shared/pipes/current-price-by-uid.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { InstrumentInList, SortModeEnum } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { LlmBuySellRateComponent } from '../../entities/llm-buy-sell-rate/llm-buy-sell-rate.component';
import { DrawerComponent } from '../../entities/drawer/drawer.component';
import { DrawerStateService } from '../../shared/services/drawer-state.service';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';


@Component({
  selector: 'table-full-3',
  imports: [
    CommonModule,
    MatTableModule,
    ScrollingModule,
    InstrumentLogoComponent,
    FundamentalsComponent,
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
  ],
  providers: [],
  templateUrl: './table-full-3.component.html',
  styleUrl: './table-full-3.component.scss'
})
export class TableFull3Component {

  isLoaded = signal<boolean>(false);
  dataSource = new TableVirtualScrollDataSource<InstrumentInList>([])

  private _sortModeService = inject(SortModeService);
  sortTickers = this._sortModeService.sortMode;

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
  protected readonly tableItemHeightPx = 265;

  displayedColumns: string[] = [
    'logo',
    'fundamental',
    'complex',
    'balance',
    'llm_buy_sell_rate',
  ];

  drawerState = inject(DrawerStateService);

  private appService = inject(ApiService);

  @ViewChild(MatSort) sort!: MatSort;

  constructor() {
    toObservable(this.sortTickers)
      .pipe(
        tap(() => this.isLoaded.set(false)),
        switchMap((sortTickers) => this.appService.getInstruments(sortTickers)),
        tap(() => this.isLoaded.set(true)),
      )
      .subscribe(instruments => this.dataSource.data = instruments);
  }

  handleChangeSort(): void {
    // persisted via SortModeService
  }

}
