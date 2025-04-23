import { Component, DestroyRef, inject, OnInit, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatIconModule } from '@angular/material/icon';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { TableVirtualScrollDataSource, TableVirtualScrollModule } from 'ng-table-virtual-scroll';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList } from '../../types';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { PredictionComponent } from '../../entities/prediction/prediction.component';
import { ForecastComponent } from '../../entities/forecast/forecast.component';
import { ForecastHistoryComponent } from '../../entities/forecast-history/forecast-history.component';
import { GraphComponent } from '../../entities/graph/graph.component';
import { CandleInterval } from '../../enums';
import { CurrentPriceByUidPipe } from '../../shared/pipes/current-price-by-uid.pipe';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { NewsComplexComponent } from '../../entities/news-complex/news-complex.component';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';


@Component({
  selector: 'table-full',
  imports: [
    CommonModule,
    MatTableModule,
    ScrollingModule,
    InstrumentLogoComponent,
    FundamentalsComponent,
    BalanceComponent,
    PredictionComponent,
    ForecastComponent,
    ForecastHistoryComponent,
    ComplexGraphComponent,
    GraphComponent,
    MatSortModule,
    RouterModule,
    TableVirtualScrollModule,
    CurrentPriceByUidPipe,
    PriceRoundPipe,
    PriceFormatPipe,
    MatIconModule,
    NewsComplexComponent,
    PreloaderComponent,
  ],
  providers: [],
  templateUrl: './table-full.component.html',
  styleUrl: './table-full.component.scss'
})
export class TableFullComponent implements OnInit {

  isLoaded = signal<boolean>(false);
  dataSource = new TableVirtualScrollDataSource<InstrumentInList>([])

  protected readonly CandleInterval = CandleInterval;
  protected readonly tableItemHeightPx = 265;

  displayedColumns: string[] = [
    'logo',
    'ticker',
    'name',
    'fundamental',
    '5years',
    'complex',
    'price',
    'balance',
    'forecast',
    'prediction',
    'news'
  ];

  private appService = inject(ApiService);

  @ViewChild(MatSort) sort!: MatSort;

  private destroyRef = inject(DestroyRef);

  ngOnInit() {
    this.loadInstrument();
  }

  private loadInstrument(): void {
    this.appService.getInstruments()
      .pipe(
        finalize(() => this.isLoaded.set(true)),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe(resp => {
        if (resp?.length) {
          this.dataSource.data = resp;
        }
      });
  }

}
