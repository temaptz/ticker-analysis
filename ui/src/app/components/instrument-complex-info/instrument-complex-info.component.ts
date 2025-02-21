import { Component, input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { PreloaderComponent } from '../../components/preloader/preloader.component';
import { Instrument } from '../../types';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs';
import { InstrumentLogoComponent } from '../instrument-logo/instrument-logo.component';
import { ComplexGraphComponent } from '../complex-graph/complex-graph.component';
import { FundamentalsComponent } from '../fundamentals/fundamentals.component';
import { GraphComponent } from '../graph/graph.component';
import { CandleInterval } from '../../enums';
import { parseJSON } from 'date-fns';
import { getPriceByQuotation } from '../../utils';
import { BalanceComponent } from '../balance/balance.component';
import { ForecastComponent } from '../forecast/forecast.component';
import { ForecastHistoryComponent } from '../forecast-history/forecast-history.component';
import { PredictionComponent } from '../prediction/prediction.component';
import { NewsComponent } from '../news/news.component';
import { CurrentPriceComponent } from '../current-price/current-price.component';


@Component({
  selector: 'instrument-complex-info',
  standalone: true,
  imports: [CommonModule, PreloaderComponent, InstrumentLogoComponent, ComplexGraphComponent, FundamentalsComponent, GraphComponent, BalanceComponent, ForecastComponent, ForecastHistoryComponent, PredictionComponent, NewsComponent, CurrentPriceComponent],
  providers: [],
  templateUrl: './instrument-complex-info.component.html',
  styleUrl: './instrument-complex-info.component.scss'
})
export class InstrumentComplexInfoComponent implements OnInit {

  instrumentUid = input.required<string>();

  instrument = signal<Instrument>(false);
  isLoaded = signal<boolean>(false);

  complexGraphHistoryDaysCount = 30 * 6

  constructor(
    private appService: AppService
  ) {}

  ngOnInit() {
    this.appService.getInstrument(this.instrumentUid())
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.instrument.set(resp));
  }

  protected readonly candleInterval = CandleInterval;
}
