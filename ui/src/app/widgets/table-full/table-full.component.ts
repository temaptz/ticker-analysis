import { Component, DestroyRef, effect, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatIconModule } from '@angular/material/icon';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { switchMap, tap } from 'rxjs';
import { TableVirtualScrollDataSource, TableVirtualScrollModule } from 'ng-table-virtual-scroll';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList } from '../../shared/types';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { DrawerComponent } from '../../entities/drawer/drawer.component';
import { PredictionComponent } from '../../entities/prediction/prediction.component';
import { ForecastComponent } from '../../entities/forecast/forecast.component';
import { ForecastHistoryComponent } from '../../entities/forecast-history/forecast-history.component';
import { CandleInterval } from '../../shared/enums';
import { CurrentPriceByUidPipe } from '../../shared/pipes/current-price-by-uid.pipe';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { NewsComplexComponent } from '../../entities/news-complex/news-complex.component';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { SortModeEnum } from '../../shared/types';
import { RecommendationComponent } from '../../entities/recommendation/recommendation.component';


@Component({
  selector: 'table-full',
  imports: [
    CommonModule,
    MatTableModule,
    ScrollingModule,
    InstrumentLogoComponent,
    FundamentalsComponent,
    DrawerComponent,
    PredictionComponent,
    ForecastComponent,
    ForecastHistoryComponent,
    ComplexGraphComponent,
    MatSortModule,
    RouterModule,
    TableVirtualScrollModule,
    CurrentPriceByUidPipe,
    PriceRoundPipe,
    PriceFormatPipe,
    MatIconModule,
    NewsComplexComponent,
    PreloaderComponent,
    BalanceComponent,
    RecommendationComponent,
  ],
  providers: [],
  templateUrl: './table-full.component.html',
  styleUrl: './table-full.component.scss'
})
export class TableFullComponent {

  isLoaded = signal<boolean>(false);
  sortTickers = signal<SortModeEnum>(SortModeEnum.Buy)
  dataSource = new TableVirtualScrollDataSource<InstrumentInList>([])

  protected readonly CandleInterval = CandleInterval;
  protected readonly tableItemHeightPx = 265;

  displayedColumns: string[] = [
    'logo',
    'ticker',
    'name',
    'fundamental',
    // '5years',
    'complex',
    'price',
    'balance',
    'forecast',
    'prediction',
    'news',
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
      this.sortTickers.set(JSON.parse(ls) ?? SortModeEnum.Buy);
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
