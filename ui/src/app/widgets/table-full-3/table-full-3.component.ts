import { Component, effect, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { Subscription, tap } from 'rxjs';
import { TableVirtualScrollDataSource, TableVirtualScrollModule } from 'ng-table-virtual-scroll';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
// import { ForecastComponent } from '../../entities/forecast/forecast.component';
// import { ForecastHistoryComponent } from '../../entities/forecast-history/forecast-history.component';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { CurrentPriceByUidPipe } from '../../shared/pipes/current-price-by-uid.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { InstrumentInList, SortModeEnum } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { NewsComplexComponent } from '../../entities/news-complex/news-complex.component';
import { LlmBuySellRateComponent } from '../../entities/llm-buy-sell-rate/llm-buy-sell-rate.component';
import { PredictionDynamicComponent } from '../../entities/prediction-dynamic/prediction-dynamic.component';
import { DrawerComponent } from '../../entities/drawer/drawer.component';


@Component({
  selector: 'table-full-3',
  imports: [
    CommonModule,
    MatTableModule,
    ScrollingModule,
    InstrumentLogoComponent,
    FundamentalsComponent,
    BalanceComponent,
    // ForecastComponent,
    // ForecastHistoryComponent,
    ComplexGraphComponent,
    MatSortModule,
    RouterModule,
    TableVirtualScrollModule,
    CurrentPriceByUidPipe,
    PriceFormatPipe,
    NewsComplexComponent,
    LlmBuySellRateComponent,
    PredictionDynamicComponent,
    DrawerComponent
  ],
  providers: [],
  templateUrl: './table-full-3.component.html',
  styleUrl: './table-full-3.component.scss'
})
export class TableFull3Component {

  isLoaded = signal<boolean>(false);
  dataSource = new TableVirtualScrollDataSource<InstrumentInList>([])
  sortTickers = signal<SortModeEnum>(SortModeEnum.BuyPerspective)

  protected readonly CandleInterval = CandleInterval;
  protected readonly tableItemHeightPx = 265;

  displayedColumns: string[] = [
    'logo',
    'fundamental',
    'complex',
    'balance',
    // 'forecast',
    'prediction',
    'news',
    'llm_buy_sell_rate',
  ];

  private appService = inject(ApiService);

  private ls = localStorage;
  private lsKey = 'sortTickers';

  private subscription?: Subscription;

  @ViewChild(MatSort) sort!: MatSort;

  constructor() {
    const ls = this.ls.getItem(this.lsKey);
    if (ls) {
      this.sortTickers.set(JSON.parse(ls) ?? SortModeEnum.BuyPerspective);
    }

    effect(() => {
      this.isLoaded.set(false);
      this.subscription?.unsubscribe();
      this.subscription = this.appService.getInstruments(this.sortTickers()).pipe(
        tap(() => this.isLoaded.set(true)),
      ).subscribe(instruments => this.dataSource.data = instruments);
    });
  }

  handleChangeSort(): void {
    this.ls.setItem(this.lsKey, JSON.stringify(this.sortTickers()));
  }

}
