import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { Instrument } from '../../types';
import { CandleInterval } from '../../enums';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { GraphComponent } from '../../entities/graph/graph.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { ForecastComponent } from '../../entities/forecast/forecast.component';
import { ForecastHistoryComponent } from '../../entities/forecast-history/forecast-history.component';
import { PredictionComponent } from '../../entities/prediction/prediction.component';
import { NewsComponent } from '../../entities/news/news.component';
import { CurrentPriceComponent } from '../../entities/current-price/current-price.component';
import { ComplexGraph2Component } from '../../entities/complex-graph-2/complex-graph-2.component';


@Component({
  selector: 'instrument-complex-info',
  imports: [CommonModule, PreloaderComponent, InstrumentLogoComponent, FundamentalsComponent, GraphComponent, BalanceComponent, ForecastComponent, ForecastHistoryComponent, PredictionComponent, NewsComponent, CurrentPriceComponent, FormsModule, ComplexGraph2Component],
  providers: [],
  templateUrl: './instrument-complex-info.component.html',
  styleUrl: './instrument-complex-info.component.scss'
})
export class InstrumentComplexInfoComponent {

  instrumentUid = input.required<string>();

  instrument = signal<Instrument>(false);
  isLoaded = signal<boolean>(false);

  complexGraphHistoryDaysCount = 180
  complexGraphFutureDaysCount = 30
  complexGraphHistoryInterval: CandleInterval = CandleInterval.CANDLE_INTERVAL_DAY;
  protected readonly candleInterval = CandleInterval;

  constructor(
    private appService: ApiService
  ) {
    effect(() => {
      const instrumentUid = this.instrumentUid();

      this.appService.getInstrument(instrumentUid)
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe(resp => this.instrument.set(resp));
    });
  }

}
