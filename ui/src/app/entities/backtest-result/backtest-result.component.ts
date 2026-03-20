import { Component, computed, inject, input, resource } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { BacktestRateResp } from '../../shared/types';
import { VerticalScaleComponent } from '../../shared/components/vertical-scale/vertical-scale.component';
import { PreloaderComponent } from '../preloader/preloader.component';
import { GRAPH_COLORS } from '../../shared/const';
import { format } from 'date-fns';

@Component({
  selector: 'backtest-result',
  imports: [CommonModule, VerticalScaleComponent, PreloaderComponent, DecimalPipe],
  templateUrl: './backtest-result.component.html',
  styleUrl: './backtest-result.component.scss'
})
export class BacktestResultComponent {
  instrumentUid = input.required<string>();
  accountId = input.required<number>();
  selectedDate = input.required<Date>();

  private apiService = inject(ApiService);

  buyColor = GRAPH_COLORS.buy;
  sellColor = GRAPH_COLORS.sell;

  rateDataResource = resource<BacktestRateResp, {uid: string, accountId: number, date: Date}>({
    defaultValue: {
      total_buy: { rate: 0, debug: {} },
      total_sell: { rate: 0, debug: {} },
    },
    params: () => ({
      uid: this.instrumentUid(),
      accountId: this.accountId(),
      date: this.selectedDate(),
    }),
    loader: (params): Promise<BacktestRateResp> => {
      if (!params?.params?.uid || !params?.params?.accountId || !params?.params?.date) {
        return Promise.resolve({
          total_buy: { rate: 0, debug: {} },
          total_sell: { rate: 0, debug: {} },
        });
      }
      return firstValueFrom(
        this.apiService.getBacktestRate(
          params.params.uid,
          params.params.accountId,
          params.params.date
        )
      );
    }
  });

  formattedDate = computed(() => {
    const date = this.selectedDate();
    return format(date, 'dd.MM.yyyy');
  });

  metrics = [
    { key: 'macd', label: 'MACD' },
    { key: 'rsi', label: 'RSI' },
    { key: 'tech', label: 'Тех. анализ' },
    { key: 'news', label: 'Новости' },
    { key: 'fundamental', label: 'Фундаментал' },
    { key: 'volume', label: 'Объём' },
    { key: 'profit', label: 'Прибыль' },
  ];
}
