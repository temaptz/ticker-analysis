import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { finalize } from 'rxjs';
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
import { MatSort } from '@angular/material/sort';


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
    MatSort,
    RouterLink
  ],
  providers: [],
  templateUrl: './table-full-2.component.html',
  styleUrl: './table-full-2.component.scss'
})
export class TableFull2Component implements OnInit {

  instruments = signal<InstrumentInList[]>([]);
  isLoaded = signal<boolean>(false);

  protected readonly CandleInterval = CandleInterval;

  displayedColumns: string[] = ['logo', 'ticker', 'name', 'fundamental', '5years', 'year', 'complex', 'price', 'balance-main', 'balance-analytics', 'forecast', 'prediction', 'news'];

  private router = inject(Router);
  private appService = inject(ApiService);

  ngOnInit() {
    this.appService.getInstruments()
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.instruments.set(resp));
  }
}
