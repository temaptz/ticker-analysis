import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { Instrument } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';
import { ForecastComponent } from '../../entities/forecast/forecast.component';
import { ForecastHistoryComponent } from '../../entities/forecast-history/forecast-history.component';
import { PredictionComponent } from '../../entities/prediction/prediction.component';
import { CurrentPriceComponent } from '../../entities/current-price/current-price.component';
import { ComplexGraphComponent } from '../../entities/complex-graph/complex-graph.component';
import { NewsComplexComponent } from '../../entities/news-complex/news-complex.component';
import { BalanceComponent } from '../../entities/balance/balance.component';
import { RecommendationComponent } from '../../entities/recommendation/recommendation.component';
import { LlmBuySellRateComponent } from '../../entities/llm-buy-sell-rate/llm-buy-sell-rate.component';
import { PredictionDynamicComponent } from '../../entities/prediction-dynamic/prediction-dynamic.component';


@Component({
  selector: 'instrument-complex-info',
  imports: [CommonModule, PreloaderComponent, InstrumentLogoComponent, FundamentalsComponent, ForecastComponent, ForecastHistoryComponent, PredictionComponent, CurrentPriceComponent, FormsModule, ComplexGraphComponent, NewsComplexComponent, BalanceComponent, RecommendationComponent, LlmBuySellRateComponent, PredictionDynamicComponent],
  providers: [],
  templateUrl: './instrument-complex-info.component.html',
  styleUrl: './instrument-complex-info.component.scss'
})
export class InstrumentComplexInfoComponent {

  instrumentUid = input.required<string>();

  instrument = signal<Instrument | null>(null);
  isLoaded = signal<boolean>(false);

  complexGraphHistoryDaysCount = 365
  complexGraphFutureDaysCount = 180
  complexGraphHistoryInterval: CandleInterval = CandleInterval.CANDLE_INTERVAL_WEEK;

  private appService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      const instrumentUid = this.instrumentUid();

      this.appService.getInstrument(instrumentUid)
        .pipe(
          finalize(() => this.isLoaded.set(true)),
          takeUntilDestroyed(this.destroyRef),
        )
        .subscribe(resp => this.instrument.set(resp));
    });
  }

}
