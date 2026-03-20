import { Component, computed, inject, input, output, resource } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { parseJSON } from 'date-fns';
import * as echarts from 'echarts';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentHistoryPrice } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';

@Component({
  selector: 'backtest-graph',
  imports: [CommonModule, EchartsGraphComponent, PreloaderComponent],
  templateUrl: './backtest-graph.component.html',
  styleUrl: './backtest-graph.component.scss'
})
export class BacktestGraphComponent {
  instrumentUid = input.required<string>();
  selectedDate = input.required<Date>();
  periodYears = input<number>(1);
  
  // Пробрасываем событие клика на графике наружу
  onChartClick = output<Date>();

  private apiService = inject(ApiService);

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

  option = computed<echarts.EChartsOption>(() => {
    return {
      ...ECHARTS_MAIN_OPTIONS,
      series: [this.seriesHistoryPrice()],
    };
  });
  
  // Обработчик клика на графике
  handleChartClick(date: Date): void {
    this.onChartClick.emit(date);
  }
}
