import {
  Component, computed,
  effect,
  input,
  numberAttribute,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { map, Observable, of, switchMap, tap } from 'rxjs';
import { addDays, endOfDay, isAfter, parseJSON, startOfDay, subDays } from 'date-fns';
import * as echarts from 'echarts';
import { ApiService } from '../../shared/services/api.service';
import { GRAPH_COLORS } from '../../shared/const';
import {
  Instrument,
  InstrumentForecastsGraphItem,
  InstrumentHistoryPrice,
  InstrumentInList,
  Operation,
  PredictionGraphResp, TechAnalysisResp
} from '../../types';
import { getPriceByQuotation, getRoundPrice } from '../../utils';
import { CandleInterval } from '../../enums';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';


@Component({
  selector: 'complex-graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [PriceFormatPipe],
  templateUrl: './complex-graph.component.html',
  styleUrl: './complex-graph.component.scss'
})
export class ComplexGraphComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  historyInterval = input<CandleInterval>(CandleInterval.CANDLE_INTERVAL_WEEK);
  daysHistory = input(90, { transform: numberAttribute });
  daysFuture = input(90, { transform: numberAttribute });
  width = input<string>('450px');
  height = input<string>('150px');
  isShowOperations = input<boolean>(false);
  isShowForecasts = input<boolean>(false);
  isShowTechAnalysis = input<boolean>(false);

  isLoadedHistoryPrice = signal<boolean>(true);
  isLoadedPredictions = signal<boolean>(true);
  isLoadedOperations = signal<boolean>(true);
  isLoadedForecasts = signal<boolean>(true);
  isLoadedTechAnalysis = signal<boolean>(true);
  isLoaded = computed<boolean>(() => (this.isLoadedHistoryPrice() && this.isLoadedPredictions() && this.isLoadedOperations() && this.isLoadedForecasts() && this.isLoadedTechAnalysis()));

  historyPrices = signal<InstrumentHistoryPrice[]>([]);
  predictionResp = signal<PredictionGraphResp | null>(null);
  operations = signal<Operation[]>([]);
  forecasts = signal<InstrumentForecastsGraphItem[]>([]);
  techAnalysis = signal<TechAnalysisResp | null>(null);

  seriesHistoryPrice = computed<echarts.SeriesOption>(() => {
    const history = this.historyPrices();

    return {
      name: 'Фактически',
      type: 'candlestick',
      barWidth: 1.5,
      itemStyle: {
        color: '#00b050',
        color0: '#ff0000',
        borderColor: '#00b050',
        borderColor0: '#ff0000',
      },
      encode: {
        x: 0,
        y: [1, 2, 3, 4]
      },
      data: history?.map(i => [
        parseJSON(i.time),                 // x
        getPriceByQuotation(i.open) ?? 0,  // open
        getPriceByQuotation(i.close) ?? 0, // close
        getPriceByQuotation(i.low) ?? 0,   // low
        getPriceByQuotation(i.high) ?? 0   // high
      ]) ?? [],
    };
  });

  seriesTa_1 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.['ta-1'] ?? [];

    return {
      name: 'Предсказания TA-1',
      type: 'line',
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 2.5,
      itemStyle: {
        color: GRAPH_COLORS.ta_1
      },
      lineStyle: {
        width: 1,
      },
      encode: {
        x: 0,
        y: 1
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction)
        ]
      ) ?? []
    };
  });

  seriesTa_1_1 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.['ta-1_1'] ?? [];

    return {
      name: 'Предсказания TA-1_1',
      type: 'line',
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 2.5,
      itemStyle: {
        color: GRAPH_COLORS.ta_1_1
      },
      lineStyle: {
        width: 1,
      },
      encode: {
        x: 0,
        y: 1
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction)
        ]
      ) ?? []
    };
  });

  seriesTa_1_2 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.['ta-1_2'] ?? [];

    return {
      name: 'Предсказания TA-1_2',
      type: 'line',
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 2.5,
      itemStyle: {
        color: GRAPH_COLORS.ta_1_2
      },
      lineStyle: {
        width: 1,
      },
      encode: {
        x: 0,
        y: 1
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction)
        ]
      ) ?? []
    };
  });

  seriesTa_2 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.['ta-2'] ?? [];

    return {
      name: 'Предсказания TA-2',
      type: 'line',
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 2.5,
      itemStyle: {
        color: GRAPH_COLORS.ta_2
      },
      lineStyle: {
        width: 1,
      },
      encode: {
        x: 0,
        y: 1
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction)
        ]
      ) ?? []
    };
  });

  seriesOperations = computed<echarts.SeriesOption>(() => {
    const operations = this.operations() ?? [];

    return {
      name: 'Операции',
      type: 'scatter',
      symbol: 'pin',
      symbolSize: 25,
      encode: {
        x: 0,
        y: 1,
        tooltip: 2,
      },
      data: operations?.map(i => {
        const isBuy = i.operation_type._name_ === 'OPERATION_TYPE_BUY'
        const tooltip =
          `${isBuy ? 'Покупка' : 'Продажа'} ${i.quantity}шт. `
          + `По цене ${this.priceFormatPipe.transform(getPriceByQuotation(i.price))}. `
          + `Всего на ${this.priceFormatPipe.transform(getPriceByQuotation(i.payment))}`;

        return {
          value: [
            parseJSON(i.date),
            getPriceByQuotation(i.price),
            tooltip,
          ],
          itemStyle: {
            color: isBuy ? '#00ff00' : '#ff0000',
          }
        };
      }) ?? []
    };
  });

  seriesForecasts = computed<echarts.SeriesOption>(() => {
    const forecasts = this.forecasts() ?? [];

    return {
      name: 'Прогнозы аналитиков',
      type: 'line',
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 2.5,
      itemStyle: {
        color: GRAPH_COLORS.forecasts
      },
      lineStyle: {
        width: 1,
      },
      encode: {
        x: 0,
        y: 1
      },
      data: forecasts?.map(i => [
        parseJSON(i.date),
        getRoundPrice(i.consensus)
      ]) ?? []
    };
  });

  seriesTechAnalysis = computed<echarts.SeriesOption[]>(() => {
    const techAnalysis = this.techAnalysis();

    return [
      // {
      //   name: 'Тех. анализ RSI',
      //   type: 'line',
      //   showSymbol: true,
      //   symbol: 'circle',
      //   symbolSize: 2.5,
      //   itemStyle: {
      //     color: GRAPH_COLORS.tech_rsi
      //   },
      //   lineStyle: {
      //     width: 1,
      //   },
      //   encode: {
      //     x: 0,
      //     y: 1
      //   },
      //   data: techAnalysis?.RSI?.map(i => [
      //     parseJSON(i.date),
      //     i.signal,
      //   ]) ?? []
      // },
      {
        name: 'Тех. анализ BB',
        type: 'line',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 2.5,
        itemStyle: {
          color: GRAPH_COLORS.tech_bb
        },
        lineStyle: {
          width: 1,
        },
        encode: {
          x: 0,
          y: 1
        },
        data: techAnalysis?.BB?.map(i => [
          parseJSON(i.date),
          i.middle_band,
        ]) ?? []
      },
      {
        name: 'Тех. анализ EMA',
        type: 'line',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 2.5,
        itemStyle: {
          color: GRAPH_COLORS.tech_ema
        },
        lineStyle: {
          width: 1,
        },
        encode: {
          x: 0,
          y: 1
        },
        data: techAnalysis?.EMA?.map(i => [
          parseJSON(i.date),
          i.signal,
        ]) ?? []
      },
      {
        name: 'Тех. анализ SMA',
        type: 'line',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 2.5,
        itemStyle: {
          color: GRAPH_COLORS.tech_sma
        },
        lineStyle: {
          width: 1,
        },
        encode: {
          x: 0,
          y: 1
        },
        data: techAnalysis?.SMA?.map(i => [
          parseJSON(i.date),
          i.signal,
        ]) ?? []
      },
      // {
      //   name: 'Тех. анализ MACD',
      //   type: 'line',
      //   showSymbol: true,
      //   symbol: 'circle',
      //   symbolSize: 2.5,
      //   itemStyle: {
      //     color: GRAPH_COLORS.tech_macd
      //   },
      //   lineStyle: {
      //     width: 1,
      //   },
      //   encode: {
      //     x: 0,
      //     y: 1
      //   },
      //   data: techAnalysis?.MACD?.map(i => [
      //     parseJSON(i.date),
      //     i.macd,
      //   ]) ?? []
      // }
    ];
  });

  option = computed<echarts.EChartsOption>(() => {
    const series: echarts.SeriesOption[] = [];

    if (this.isLoadedHistoryPrice()) {
      series.push(this.seriesHistoryPrice());
    }

    if (this.isLoadedPredictions()) {
      series.push(
        this.seriesTa_1(),
        this.seriesTa_1_1(),
        this.seriesTa_1_2(),
        this.seriesTa_2(),
      );
    }

    if (this.isLoadedOperations()) {
      series.push(this.seriesOperations());
    }

    if (this.isLoadedForecasts()) {
      series.push(this.seriesForecasts());
    }

    if (this.isLoadedTechAnalysis()) {
      series.push(...this.seriesTechAnalysis());
    }

    return {
      ...ECHARTS_MAIN_OPTIONS,
      legend: {
        show: true,
      },
      series,
    }
  });

  constructor(
    private appService: ApiService,
    private priceFormatPipe: PriceFormatPipe,
  ) {
    effect(() => {
      const uid = this.instrumentUid();
      const historyDays = this.daysHistory();
      const interval = this.historyInterval();

      of(undefined)
        .pipe(
          tap(() => this.isLoadedHistoryPrice.set(false)),
          switchMap(() => this.appService.getInstrumentHistoryPrices(
            uid,
            historyDays,
            interval
          )),
          tap(() => this.isLoadedHistoryPrice.set(true)),
        )
        .subscribe((resp: InstrumentHistoryPrice[]) => this.historyPrices.set(resp));
    });

    effect(() => {
      const uid = this.instrumentUid();
      const historyDays = this.daysHistory();
      const futureDays = this.daysFuture();
      const interval = this.historyInterval();

      of(undefined)
        .pipe(
          tap(() => this.isLoadedPredictions.set(false)),
          switchMap(() => this.appService.getInstrumentPredictionGraph(
            uid,
            startOfDay(subDays(new Date(), historyDays)),
            endOfDay(addDays(new Date(), futureDays)),
            interval,
          )),
          tap(() => this.isLoadedPredictions.set(true)),
        )
        .subscribe((resp: PredictionGraphResp) => this.predictionResp.set(resp));
    });

    effect(() => {
      const historyDays = this.daysHistory();
      const isShowOperations = this.isShowOperations();

      of(undefined)
        .pipe(
          tap(() => this.isLoadedOperations.set(false)),
          switchMap(() => isShowOperations
            ? this.appService.getInstrument(this.instrumentUid())
              .pipe(
                switchMap((instrument: Instrument) =>
                  this.appService.getInstrumentOperations(instrument.figi)
                ),
                map((operations: Operation[]) => {
                  const from = subDays(new Date(), historyDays);
                  return operations.filter(i => isAfter(parseJSON(i.date), from));
                }),
              )
            : of([])
          ),
          tap(() => this.isLoadedOperations.set(true)),
        )
        .subscribe((resp: Operation[]) => this.operations.set(resp));
    });

    effect(() => {
      const historyDays = this.daysHistory();
      const futureDays = this.daysFuture();
      const interval = this.historyInterval();
      const isShowForecasts = this.isShowForecasts();

      of(undefined)
        .pipe(
          tap(() => this.isLoadedForecasts.set(false)),
          switchMap(() => isShowForecasts
            ? this.appService.getInstrumentForecastsGraph(
              this.instrumentUid(),
              startOfDay(subDays(new Date(), historyDays)),
              endOfDay(addDays(new Date(), futureDays)),
              interval,
            )
            : of([])
          ),
          tap(() => this.isLoadedForecasts.set(true)),
        )
        .subscribe((resp: InstrumentForecastsGraphItem[]) => this.forecasts.set(resp));
    });

    effect(() => {
      const uid = this.instrumentUid();
      const historyDays = this.daysHistory();
      const futureDays = this.daysFuture();
      const interval = this.historyInterval();

      of(undefined)
        .pipe(
          tap(() => this.isLoadedTechAnalysis.set(false)),
          switchMap(() => this.appService.getInstrumentTechGraph(
            uid,
            startOfDay(subDays(new Date(), historyDays)),
            endOfDay(addDays(new Date(), futureDays)),
            interval
          )),
          tap(() => this.isLoadedTechAnalysis.set(true)),
        )
        .subscribe((resp: TechAnalysisResp) => this.techAnalysis.set(resp));
    });
  }

}

