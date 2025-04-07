import {
  Component,
  effect,
  ElementRef,
  input,
  numberAttribute,
  signal,
  ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { combineLatest, finalize, map, Observable, of, switchMap } from 'rxjs';
import { addDays, endOfDay, isAfter, parseJSON, startOfDay, subDays } from 'date-fns';
import * as echarts from 'echarts';
import { ApiService } from '../../shared/services/api.service';
import { GRAPH_COLORS } from '../../shared/const';
import { Instrument, InstrumentHistoryPrice, InstrumentInList, Operation, PredictionGraphResp } from '../../types';
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
  historyInterval = input<CandleInterval>(CandleInterval.CANDLE_INTERVAL_DAY);
  daysHistory = input(90, { transform: numberAttribute });
  daysFuture = input(90, { transform: numberAttribute });
  width = input<string>('450px');
  height = input<string>('150px');
  isShowOperations = input<boolean>(false);

  isLoaded = signal<boolean>(false);
  option = signal<echarts.EChartsOption | null>(null);

  @ViewChild('chart')
  private chartElRef?: ElementRef<HTMLDivElement>;

  constructor(
    private appService: ApiService,
    private priceFormatPipe: PriceFormatPipe,
  ) {
    effect(() => {
      const uid = this.instrumentUid();
      const history = this.daysHistory();
      const future = this.daysFuture();
      const interval = this.historyInterval();
      const isShowOperations = this.isShowOperations();

      combineLatest([
        this.appService.getInstrumentHistoryPrices(
          uid,
          history,
          interval
        ),
        this.appService.getInstrumentPredictionGraph(
          uid,
          startOfDay(subDays(new Date(), history)),
          endOfDay(addDays(new Date(), future)),
          interval,
        ),
        isShowOperations
          ? this.getOperations()
          : of([])
      ])
        .pipe(
          finalize(() => this.isLoaded.set(true))
        )
        .subscribe((resp: [InstrumentHistoryPrice[], PredictionGraphResp, Operation[]]) => {
          const respHistory = resp?.[0];
          const respPredictions = resp?.[1];
          const respOperations = resp?.[2];
          this.initOption(respHistory, respPredictions, respOperations);
        });
    });
  }

  private getOperations(): Observable<Operation[]> {
    return this.appService.getInstrument(this.instrumentUid())
      .pipe(
        switchMap((instrument: Instrument) => combineLatest([
          this.appService.getInstrumentOperations('Основной', instrument.figi),
          this.appService.getInstrumentOperations('Аналитический', instrument.figi),
        ])),
        map(([main, analytics]: [Operation[], Operation[]]) => {
          const allOperations = [...(main ?? []), ...(analytics ?? [])];
          const from = subDays(new Date(), this.daysHistory());

          return allOperations.filter(i => isAfter(parseJSON(i.date), from));
        }),
      )
  }

  private initOption(
    history: InstrumentHistoryPrice[],
    predictions: PredictionGraphResp,
    operations: Operation[],
  ): void {
    const option: echarts.EChartsOption = {
      ...ECHARTS_MAIN_OPTIONS,
      series: [
        {
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
        },
        {
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
          data: predictions?.['ta-1']?.map(i => [
            parseJSON(i.date),
            getRoundPrice(i.prediction
            )]) ?? []
        },
        {
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
          data: predictions?.['ta-1_1']?.map(i => [
            parseJSON(i.date),
            getRoundPrice(i.prediction)
          ]) ?? []
        },
        {
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
        }
      ]
    };

    this.option.set(option);
  }

}

