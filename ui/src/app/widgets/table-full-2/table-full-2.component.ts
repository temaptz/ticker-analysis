import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { MatSortModule } from '@angular/material/sort';
import { finalize } from 'rxjs';
import { TableVirtualScrollDataSource, TableVirtualScrollModule } from 'ng-table-virtual-scroll';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList } from '../../types';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { NewsComponent } from '../../entities/news/news.component';
import { PredictionComponent } from '../../entities/prediction/prediction.component';
import { ForecastComponent } from '../../entities/forecast/forecast.component';
import { ForecastHistoryComponent } from '../../entities/forecast-history/forecast-history.component';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { GraphComponent } from '../../entities/graph/graph.component';
import { CandleInterval } from '../../enums';
import { CurrentPriceByUidPipe } from '../../shared/pipes/current-price-by-uid.pipe';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';


@Component({
  selector: 'table-full-2',
  imports: [
    CommonModule,
    MatTableModule,
    ScrollingModule,
    InstrumentLogoComponent,
    FundamentalsComponent,
    BalanceComponent,
    NewsComponent,
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
    PriceFormatPipe
  ],
  providers: [],
  templateUrl: './table-full-2.component.html',
  styleUrl: './table-full-2.component.scss'
})
export class TableFull2Component implements OnInit {

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
    'year',
    'complex',
    'price',
    'balance-main',
    'balance-analytics',
    'forecast',
    'prediction',
    'news'
  ];

  private appService = inject(ApiService);

  ngOnInit() {
    this.appService.getInstruments()
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => {
        if (resp?.length) {
          this.dataSource.data = resp;
        }
      });
  }
}
