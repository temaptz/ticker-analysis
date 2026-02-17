import { Component, effect, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatSort } from '@angular/material/sort';
import { MatIconModule } from '@angular/material/icon';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { switchMap, tap } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, SortModeEnum } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { CurrentPriceByUidPipe } from '../../shared/pipes/current-price-by-uid.pipe';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { DrawerComponent } from '../../entities/drawer/drawer.component';
import { PredictionComponent } from '../../entities/prediction/prediction.component';
import { ForecastComponent } from '../../entities/forecast/forecast.component';
import { ForecastHistoryComponent } from '../../entities/forecast-history/forecast-history.component';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { NewsComplexComponent } from '../../entities/news-complex/news-complex.component';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { LlmBuySellRateComponent } from '../../entities/llm-buy-sell-rate/llm-buy-sell-rate.component';
import { PredictionDynamicComponent } from '../../entities/prediction-dynamic/prediction-dynamic.component';


@Component({
  selector: 'table-full',
  imports: [
    CommonModule,
    MatTableModule,
    InstrumentLogoComponent,
    FundamentalsComponent,
    DrawerComponent,
    ForecastComponent,
    ForecastHistoryComponent,
    ComplexGraphComponent,
    RouterModule,
    CurrentPriceByUidPipe,
    PriceFormatPipe,
    MatIconModule,
    NewsComplexComponent,
    PreloaderComponent,
    BalanceComponent,
    LlmBuySellRateComponent,
    PredictionDynamicComponent,
  ],
  providers: [],
  templateUrl: './table-full.component.html',
  styleUrl: './table-full.component.scss'
})
export class TableFullComponent {

  isLoaded = signal<boolean>(false);
  sortTickers = signal<SortModeEnum>(SortModeEnum.BuyPerspective)
  dataSource = new MatTableDataSource<InstrumentInList>([])

  protected readonly CandleInterval = CandleInterval;
  protected readonly tableItemHeightPx = 265;

  displayedColumns: string[] = [
    'logo',
    'fundamental',
    'complex',
    'balance',
    'forecast',
    'prediction',
    'news',
    'llm_buy_sell_rate',
  ];

  private appService = inject(ApiService);

  private ls = localStorage;
  private lsKey = 'sortTickers';

  @ViewChild(MatSort) sort!: MatSort;

  private instruments = toSignal(
    toObservable(this.sortTickers).pipe(
      tap(() => this.isLoaded.set(false)),
      switchMap(sort => this.appService.getInstruments(sort)),
      tap(() => this.isLoaded.set(true)),
    ), {initialValue: []}
  )

  constructor() {
    const ls = this.ls.getItem(this.lsKey);
    if (ls) {
      this.sortTickers.set(JSON.parse(ls) ?? SortModeEnum.BuyPerspective);
    }

    effect(() => {
      const instruments = this.instruments();
      this.dataSource.data = instruments ?? [];
    });
  }

  handleChangeSort(): void {
    this.ls.setItem(this.lsKey, JSON.stringify(this.sortTickers()));
  }

}
