import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { Instrument, InstrumentInList } from '../../types';
import { parseJSON } from 'date-fns';
import { GraphComponent } from '../graph/graph.component';
import { CandleInterval } from '../../enums';
import { getPriceByQuotation } from '../../utils';
import { ForecastComponent } from '../forecast/forecast.component';
import { ForecastHistoryComponent } from '../forecast-history/forecast-history.component';
import { FundamentalsComponent } from '../fundamentals/fundamentals.component';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PredictionComponent } from '../prediction/prediction.component';
import { ComplexGraphComponent } from '../complex-graph/complex-graph.component';
import { BalanceComponent } from '../balance/balance.component';
import { NewsComponent } from '../news/news.component';
import { RouterLink } from '@angular/router';
import { InstrumentLogoComponent } from '../instrument-logo/instrument-logo.component';


@Component({
    selector: '[app-table-row]',
    imports: [CommonModule, GraphComponent, ForecastComponent, ForecastHistoryComponent, FundamentalsComponent, PreloaderComponent, PredictionComponent, ComplexGraphComponent, BalanceComponent, NewsComponent, RouterLink, InstrumentLogoComponent],
    templateUrl: './table-row.component.html',
    styleUrl: './table-row.component.scss'
})
export class TableRowComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  isLoadedInstrument = signal<boolean>(false);
  isLoadedPrice = signal<boolean>(false);
  instrument = signal<Instrument>(null);
  instrumentLastPrice = signal<number | null>(null);
  candleInterval = CandleInterval;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrument(this.instrumentUid)
      .pipe(finalize(() => this.isLoadedPrice.set(true)))
      .subscribe(resp => this.instrument.set(resp));

    this.appService.getInstrumentLastPrices(this.instrumentUid)
      .pipe(finalize(() => this.isLoadedInstrument.set(true)))
      .subscribe(resp => {
        const price = resp
          ?.sort((a, b) => parseJSON(a.time).getTime() - parseJSON(b.time).getTime())
          ?.[0];

        this.instrumentLastPrice.set(getPriceByQuotation(price.price));
      });
  }

}
