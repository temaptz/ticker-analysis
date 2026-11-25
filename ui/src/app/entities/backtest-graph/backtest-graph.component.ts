import { Component, computed, inject, input, output, resource } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom, switchMap, map } from 'rxjs';
import { isAfter, parseJSON, subDays } from 'date-fns';
import * as echarts from 'echarts';
import { ApiService } from '../../shared/services/api.service';
import { Instrument, InstrumentHistoryPrice, Operation } from '../../shared/types';
import { CandleInterval, OperationTypeEnum } from '../../shared/enums';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';

@Component({
  selector: 'backtest-graph',
  imports: [CommonModule, EchartsGraphComponent, PreloaderComponent],
  providers: [PriceFormatPipe],
  templateUrl: './backtest-graph.component.html',
  styleUrl: './backtest-graph.component.scss'
})
export class BacktestGraphComponent {
  instrumentUid = input.required<string>();
  selectedDate = input.required<Date>();
  periodYears = input<number>(1);
  accountId = input<number>();
  
  // Пробрасываем событие клика на графике наружу
  onChartClick = output<Date>();

  private apiService = inject(ApiService);
  private priceFormatPipe = inject(PriceFormatPipe);

  daysCount = computed(() => this.periodYears() * 365);

  historyPricesResource = resource<InstrumentHistoryPrice[], {uid: string, days: number}>({
    defaultValue: [],
    params: () => ({
      uid: this.instrumentUid(),
      days: this.daysCount(),
    }),
    loader: (params): Promise<InstrumentHistoryPrice[]> => {
      if (!params?.params?.uid || !params?.params?.days) {
        return Promise.resolve([]);
      }
      return firstValueFrom(
        this.apiService.getInstrumentHistoryPrices(params.params.uid, params.params.days, CandleInterval.CANDLE_INTERVAL_DAY)
      );
    }
  });

  operationsResource = resource<Operation[], {uid: string, days: number, accountId: number | undefined}>({
    defaultValue: [],
    params: () => ({
      uid: this.instrumentUid(),
      days: this.daysCount(),
      accountId: this.accountId(),
    }),
    loader: (params): Promise<Operation[]> => {
      if (!params?.params?.uid || !params?.params?.accountId) {
        return Promise.resolve([]);
      }
      const from = subDays(new Date(), params.params.days);
      return firstValueFrom(
        this.apiService.getInstrument(params.params.uid).pipe(
          switchMap((instrument: Instrument) =>
            this.apiService.getInstrumentOperations(instrument.figi, params.params.accountId!)
          ),
          map((operations: Operation[]) =>
            operations.filter(i => isAfter(parseJSON(i.date), from))
          ),
        )
      );
    }
  });

  seriesHistoryPrice = computed<echarts.SeriesOption>(() => {
    const history = this.historyPricesResource.value();

    return {
      name: 'Цена',
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
        parseJSON(i.time),
        getPriceByQuotation(i.open) ?? 0,
        getPriceByQuotation(i.close) ?? 0,
        getPriceByQuotation(i.low) ?? 0,
        getPriceByQuotation(i.high) ?? 0
      ]) ?? [],
      markLine: {
        symbol: 'none',
        data: [{
          name: 'Выбранная дата',
          xAxis: this.selectedDate()?.toISOString(),
          lineStyle: {
            color: '#333',
            width: 2,
            type: 'solid',
          },
          label: {
            show: false,
          },
        }],
      },
    } as echarts.SeriesOption;
  });

  seriesOperations = computed<echarts.SeriesOption>(() => {
    const operations = this.operationsResource.value() ?? [];

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
        const isBuy = i.operation_type === OperationTypeEnum.Buy
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
            color: isBuy ?  '#00ff00' : '#ff0000',
          }
        };
      }) ?? []
    } as echarts.SeriesOption;
  });

  option = computed<echarts.EChartsOption>(() => {
    const series: echarts.SeriesOption[] = [this.seriesHistoryPrice()];

    if (this.accountId()) {
      series.push(this.seriesOperations());
    }

    return {
      ...ECHARTS_MAIN_OPTIONS,
      series,
    };
  });
  
  // Обработчик клика на графике
  handleChartClick(date: Date): void {
    this.onChartClick.emit(date);
  }
}
