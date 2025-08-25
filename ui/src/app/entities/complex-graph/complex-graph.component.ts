import {
  input,
  effect,
  inject,
  signal,
  computed,
  Component,
  numberAttribute,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { combineLatest, debounceTime, map, of, switchMap, tap } from 'rxjs';
import { addDays, endOfDay, isAfter, parseJSON, startOfDay, subDays } from 'date-fns';
import * as echarts from 'echarts';
import { ApiService } from '../../shared/services/api.service';
import { GRAPH_COLORS } from '../../shared/const';
import {
  Operation,
  Instrument,
  InstrumentInList,
  TechAnalysisResp,
  TechAnalysisOptions,
  PredictionGraphResp,
  InstrumentHistoryPrice,
  PredictionHistoryGraphResp,
  InstrumentForecastsGraphItem
} from '../../shared/types';
import { getPriceByQuotation, getRoundPrice } from '../../utils';
import { CandleInterval, ModelNameEnum } from '../../shared/enums';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';
import {
  ComplexGraphControlComponent,
  ComplexGraphControlOptions
} from '../complex-graph-control/complex-graph-control.component';
import { NewsGraphComponent } from '../news-graph/news-graph.component';


@Component({
  selector: 'complex-graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent, ComplexGraphControlComponent, NewsGraphComponent],
  providers: [PriceFormatPipe],
  templateUrl: './complex-graph.component.html',
  styleUrl: './complex-graph.component.scss'
})
export class ComplexGraphComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  instrumentTicker = input<string>();
  interval = input<CandleInterval>(CandleInterval.CANDLE_INTERVAL_WEEK);
  historyDaysCount = input(90, { transform: numberAttribute });
  futureDaysCount = input(90, { transform: numberAttribute });
  width = input<string>('450px');
  height = input<string>('150px');
  isShowOperations = input<boolean>(false);
  isShowForecasts = input<boolean>(false);
  isShowTechAnalysis = input<boolean>(false);
  isShowLegend = input<boolean>(false);
  isShowControl = input<boolean>(true);
  isShowPredictionsHistoryInput = input<boolean>(false);
  isShowNewsGraphInput = input<boolean>(false);
  isShowModelsGraphInput = input<boolean>(false);

  historyInterval = signal<CandleInterval>(CandleInterval.CANDLE_INTERVAL_WEEK);
  daysHistory = signal<number>(90);
  daysFuture = signal<number>(90);
  isShowNewsGraph = signal<boolean>(false);
  isShowPredictionsHistory = signal<boolean>(false);
  isShowModelsGraph = signal<boolean>(false);
  isLoadedHistoryPrice = signal<boolean>(true);
  isLoadedPredictions = signal<boolean>(true);
  isLoadedOperations = signal<boolean>(true);
  isLoadedForecasts = signal<boolean>(true);
  isLoadedTechAnalysis = signal<boolean>(true);
  isLoadedPredictionsHistory = signal<boolean>(true);
  isLoaded = computed<boolean>(() => (this.isLoadedHistoryPrice() && this.isLoadedPredictions() && this.isLoadedOperations() && this.isLoadedForecasts() && this.isLoadedTechAnalysis() && this.isLoadedPredictionsHistory()));

  techAnalysisOptions = signal<TechAnalysisOptions>({});

  historyPrices = toSignal<InstrumentHistoryPrice[]>(
    combineLatest([
      toObservable(this.instrumentUid),
      toObservable(this.daysHistory),
      toObservable(this.historyInterval),
    ])
      .pipe(
        debounceTime(0),
        tap(() => this.isLoadedHistoryPrice.set(false)),
        switchMap(([uid, historyDays, interval]) => this.appService.getInstrumentHistoryPrices(
          uid,
          historyDays,
          interval
        )),
        tap(() => this.isLoadedHistoryPrice.set(true)),
      )
  );

  predictionResp = toSignal<PredictionGraphResp | null>(
    combineLatest([
      toObservable(this.instrumentUid),
      toObservable(this.daysHistory),
      toObservable(this.daysFuture),
      toObservable(this.historyInterval),
      toObservable(this.isShowModelsGraph),
    ])
      .pipe(
        debounceTime(0),
        tap(() => this.isLoadedPredictions.set(false)),
        switchMap(([uid, historyDays, futureDays, interval, isShowModels]) => this.appService.getInstrumentPredictionGraph(
          uid,
          startOfDay(subDays(new Date(), historyDays)),
          endOfDay(addDays(new Date(), futureDays)),
          interval,
          isShowModels
            ? [
              ModelNameEnum.Ta_1,
              ModelNameEnum.Ta_1_1,
              ModelNameEnum.Ta_1_2,
              ModelNameEnum.Ta_2,
              ModelNameEnum.Ta_2_1,
              ModelNameEnum.Consensus,
            ]
            : [ModelNameEnum.Consensus]
        )),
        tap(() => this.isLoadedPredictions.set(true)),
      )
  );

  operations = toSignal<Operation[]>(
    combineLatest([
      toObservable(this.instrumentUid),
      toObservable(this.daysHistory),
      toObservable(this.isShowOperations),
    ])
      .pipe(
        debounceTime(0),
        tap(() => this.isLoadedOperations.set(false)),
        switchMap(([uid, daysHistory, isShowOperations]) => isShowOperations
          ? this.appService.getInstrument(uid)
            .pipe(
              switchMap((instrument: Instrument) =>
                this.appService.getInstrumentOperations(instrument.figi)
              ),
              map((operations: Operation[]) => {
                const from = subDays(new Date(), daysHistory);
                return operations.filter(i => isAfter(parseJSON(i.date), from));
              }),
            )
          : of([])
        ),
        tap(() => this.isLoadedOperations.set(true)),
      )
  );

  forecasts = toSignal<InstrumentForecastsGraphItem[]>(
    combineLatest([
      toObservable(this.daysHistory),
      toObservable(this.daysFuture),
      toObservable(this.historyInterval),
      toObservable(this.isShowForecasts),
    ])
      .pipe(
        debounceTime(0),
        tap(() => this.isLoadedForecasts.set(false)),
        switchMap(([historyDays, futureDays, interval, isShowForecasts]) => isShowForecasts
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
  );

  techAnalysis = toSignal<TechAnalysisResp | null>(
    combineLatest([
      toObservable(this.instrumentUid),
      toObservable(this.daysHistory),
      toObservable(this.daysFuture),
      toObservable(this.historyInterval),
      toObservable(this.isShowTechAnalysis),
    ])
      .pipe(
        debounceTime(0),
        tap(() => this.isLoadedTechAnalysis.set(false)),
        switchMap(([uid, historyDays, futureDays, interval, isShowTechAnalysis]) => isShowTechAnalysis
          ? this.appService.getInstrumentTechGraph(
            uid,
            startOfDay(subDays(new Date(), historyDays)),
            endOfDay(addDays(new Date(), futureDays)),
            interval
          )
          : of(null)
        ),
        tap(() => this.isLoadedTechAnalysis.set(true)),
      )
  );

  predictionsHistoryGraphResp = toSignal<PredictionHistoryGraphResp | null>(
    combineLatest([
      toObservable(this.instrumentUid),
      toObservable(this.daysHistory),
      toObservable(this.daysFuture),
      toObservable(this.historyInterval),
      toObservable(this.isShowPredictionsHistory),
    ])
      .pipe(
        debounceTime(0),
        tap(() => this.isLoadedPredictionsHistory.set(false)),
        switchMap(([uid, historyDays, futureDays, interval, isShowPredictionsHistory]) => isShowPredictionsHistory
          ? this.appService.getInstrumentPredictionHistoryGraph(
            uid,
            startOfDay(subDays(new Date(), historyDays)),
            endOfDay(addDays(new Date(), futureDays)),
            interval,
          )
          : of(null)
        ),
        tap(() => this.isLoadedPredictionsHistory.set(true)),
      )
  );

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
        y: [1, 2, 3, 4],
      },
      data: history?.map(i => [
        parseJSON(i.time),                 // x
        getPriceByQuotation(i.open) ?? 0,  // open
        getPriceByQuotation(i.close) ?? 0, // close
        getPriceByQuotation(i.low) ?? 0,   // low
        getPriceByQuotation(i.high) ?? 0   // high
      ]) ?? [],
    } as echarts.SeriesOption;
  });

  seriesTa_1 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.[ModelNameEnum.Ta_1] ?? [];

    return {
      name: 'Предсказания TA_1',
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
        y: 1,
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction > 0 ? i.prediction : 0),
        ]
      ) ?? []
    } as echarts.SeriesOption;
  });

  seriesTa_1_1 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.[ModelNameEnum.Ta_1_1] ?? [];

    return {
      name: 'Предсказания TA_1_1',
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
        y: 1,
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction > 0 ? i.prediction : 0),
        ]
      ) ?? []
    } as echarts.SeriesOption;
  });

  seriesTa_1_2 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.[ModelNameEnum.Ta_1_2] ?? [];

    return {
      name: 'Предсказания TA_1_2',
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
        y: 1,
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction > 0 ? i.prediction : 0),
        ]
      ) ?? []
    } as echarts.SeriesOption;
  });

  seriesTa_2 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.[ModelNameEnum.Ta_2] ?? [];

    return {
      name: 'Предсказания TA_2',
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
          getRoundPrice(i.prediction > 0 ? i.prediction : 0),
        ]
      ) ?? []
    } as echarts.SeriesOption;
  });

  seriesTa_2_1 = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.[ModelNameEnum.Ta_2_1] ?? [];

    return {
      name: 'Предсказания TA_2_1',
      type: 'line',
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 2.5,
      itemStyle: {
        color: GRAPH_COLORS.ta_2_1
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
          getRoundPrice(i.prediction > 0 ? i.prediction : 0),
        ]
      ) ?? []
    } as echarts.SeriesOption;
  });

  seriesConsensus = computed<echarts.SeriesOption>(() => {
    const predictions = this.predictionResp()?.[ModelNameEnum.Consensus] ?? [];

    return {
      name: 'Предсказания CONSENSUS',
      type: 'line',
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 2.5,
      itemStyle: {
        color: GRAPH_COLORS.consensus
      },
      lineStyle: {
        width: 3,
      },
      encode: {
        x: 0,
        y: 1
      },
      data: predictions?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction > 0 ? i.prediction : 0),
        ]
      ) ?? []
    } as echarts.SeriesOption;
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
    } as echarts.SeriesOption;
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
    } as echarts.SeriesOption;
  });

  seriesTechAnalysis = computed<echarts.SeriesOption[]>(() => {
    const techAnalysis = this.techAnalysis();
    const techAnalysisOptions = this.techAnalysisOptions();
    const result: echarts.SeriesOption[] = [];

    if (techAnalysisOptions?.isShowRSI) {
      result.push({
        name: 'Тех. анализ RSI',
        type: 'line',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 2.5,
        itemStyle: {
          color: GRAPH_COLORS.tech_rsi
        },
        lineStyle: {
          width: 1,
        },
        encode: {
          x: 0,
          y: 1
        },
        data: techAnalysis?.RSI?.map(i => [
          parseJSON(i.date),
          i.signal,
        ]) ?? []
      });
    }

    if (techAnalysisOptions?.isShowBB) {
      result.push({
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
      });
    }

    if (techAnalysisOptions.isShowEMA) {
      result.push({
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
      });
    }

    if (techAnalysisOptions.isShowSMA) {
      result.push({
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
      });
    }

    if (techAnalysisOptions.isShowMACD) {
      result.push({
        name: 'Тех. анализ MACD',
        type: 'line',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 2.5,
        itemStyle: {
          color: GRAPH_COLORS.tech_macd
        },
        lineStyle: {
          width: 1,
        },
        encode: {
          x: 0,
          y: 1
        },
        data: techAnalysis?.MACD?.map(i => [
          parseJSON(i.date),
          i.macd,
        ]) ?? []
      });
    }

    return result;
  });

  seriesPredictionsHistory = computed<echarts.SeriesOption[]>(() => {
    const graphResp = this.predictionsHistoryGraphResp();

    return Object.keys(graphResp ?? {}).map((date: string) => {
      return {
        name: `История TA_2 [${date}]`,
        type: 'line',
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 2.5,
        itemStyle: {
          color: GRAPH_COLORS.history,
        },
        lineStyle: {
          width: 1,
        },
        encode: {
          x: 0,
          y: 1,
        },
        data: graphResp?.[date]?.map(i => [
          parseJSON(i.date),
          getRoundPrice(i.prediction > 0 ? i.prediction : 0),
        ]) ?? []
      };
    });
  });

  option = computed<echarts.EChartsOption>(() => {
    const series: echarts.SeriesOption[] = [];

    if (this.isLoadedHistoryPrice()) {
      series.push(this.seriesHistoryPrice());
    }

    if (this.isLoadedPredictions()) {
      series.push(
        this.seriesConsensus(),
      );

      if (this.isShowModelsGraph()) {
        series.push(
          this.seriesTa_1(),
          this.seriesTa_1_1(),
          this.seriesTa_1_2(),
          this.seriesTa_2(),
          this.seriesTa_2_1(),
        );
      }
    }

    if (this.isShowOperations() && this.isLoadedOperations()) {
      series.push(this.seriesOperations());
    }

    if (this.isShowForecasts() && this.isLoadedForecasts()) {
      series.push(this.seriesForecasts());
    }

    if (this.isShowTechAnalysis() && this.isLoadedTechAnalysis()) {
      series.push(...this.seriesTechAnalysis());
    }

    if (this.isShowPredictionsHistory() && this.isLoadedPredictionsHistory()) {
      series.push(...this.seriesPredictionsHistory());
    }

    return {
      ...ECHARTS_MAIN_OPTIONS,
      legend: {
        show: this.isShowLegend(),
      },
      series,
    }
  });

  private appService = inject(ApiService);
  private priceFormatPipe = inject(PriceFormatPipe);

  constructor() {
    effect(() => {
      this.daysHistory.set(this.historyDaysCount());
      this.historyInterval.set(this.interval());
      this.daysFuture.set(this.futureDaysCount());
      this.isShowNewsGraph.set(this.isShowNewsGraphInput());
      this.isShowPredictionsHistory.set(this.isShowPredictionsHistoryInput());
      this.isShowModelsGraph.set(this.isShowModelsGraphInput());
    });
  }

  handleChangeControl(options: ComplexGraphControlOptions): void {
    if (options.historyDaysCount !== this.daysHistory()) {
      this.daysHistory.set(options.historyDaysCount);
    }

    if (options.interval !== this.historyInterval()) {
      this.historyInterval.set(options.interval);
    }

    if (options.futureDaysCount !== this.daysFuture()) {
      this.daysFuture.set(options.futureDaysCount);
    }

    if (options.isShowNews !== this.isShowNewsGraph()) {
      this.isShowNewsGraph.set(options.isShowNews);
    }

    if (options.isShowPredictionsHistory !== this.isShowPredictionsHistory()) {
      this.isShowPredictionsHistory.set(options.isShowPredictionsHistory);
    }

    if (options.isShowModels !== this.isShowModelsGraph()) {
      this.isShowModelsGraph.set(options.isShowModels);
    }
  }

  handleChangeTechAnalysis(options: TechAnalysisOptions): void {
    this.techAnalysisOptions.set({...options});
  }

}

