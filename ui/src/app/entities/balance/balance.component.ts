import { Component, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize, combineLatest } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, InvestCalc, Operation } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceByQuotationPipe } from '../../shared/pipes/price-by-quotation.pipe';
import { CurrentPriceService } from '../../shared/services/current-price.service';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';


@Component({
    selector: 'balance',
  imports: [CommonModule, PreloaderComponent, PriceByQuotationPipe, PriceFormatPipe],
    providers: [],
    templateUrl: './balance.component.html',
    styleUrl: './balance.component.scss'
})
export class BalanceComponent {

  accountName = input.required<string>();
  instrumentUid = input.required<InstrumentInList['uid']>();
  instrumentFigi = input.required<InstrumentInList['figi']>();

  isLoaded = signal<boolean>(false);
  operations = signal<Operation[]>([]);
  balanceQty = signal<number | null>(null);
  marketValue = signal<number | null>(null);
  potentialProfit = signal<number | null>(null);
  potentialProfitPercent = signal<number | null>(null);
  avgPrice = signal<number | null>(null);
  currentPrice = signal<number | null>(null);
  getPriceByQuotation = getPriceByQuotation;

  private apiService = inject(ApiService);

  constructor() {
    effect(() => this.apiService.getInvestCalc(this.accountName(), this.instrumentUid())
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((investCalc: InvestCalc) => {
        if (investCalc?.balance) {
          this.balanceQty.set(investCalc.balance);
        }

        if (investCalc?.current_price) {
          this.currentPrice.set(investCalc.current_price);
        }

        if (investCalc?.market_value) {
          this.marketValue.set(investCalc.market_value);
        }

        if (investCalc?.potential_profit) {
          this.potentialProfit.set(investCalc.potential_profit);
        }

        if (investCalc?.potential_profit_percent) {
          this.potentialProfitPercent.set(investCalc.potential_profit_percent);
        }

        if (investCalc?.avg_price) {
          this.avgPrice.set(investCalc.avg_price);
        }

        if (investCalc?.operations) {
          this.operations.set(investCalc.operations);
        }
      }));
  }

  /**
   * Возвращает среднюю цену покупки (Average Price) для текущего остатка бумаг.
   * Если после всех операций бумаг не осталось, вернёт 0.
   */
  private getAveragePrice(operations: Operation[]): number {
    // Храним "открытые лоты" (позиции), которые ещё не были полностью проданы.
    // Каждый элемент массива: {quantity, costPerShare}
    // - количество бумаг в данном лоте
    // - цена покупки за бумагу (при BUY).
    const openPositions: { quantity: number; costPerShare: number }[] = [];

    for (const o of operations) {
      if (o.operation_type._name_ === 'OPERATION_TYPE_BUY') {
        // При покупке добавляем новый лот.
        openPositions.push({
          quantity: o.quantity,
          costPerShare: getPriceByQuotation(o.price) ?? 0
        });
      } else if (o.operation_type === 'OPERATION_TYPE_SELL') {
        // При продаже уменьшаем лоты с начала (FIFO)
        let remainToSell = o.quantity;

        // Пока нужно что-то "продать" и есть открытые лоты
        while (remainToSell > 0 && openPositions.length > 0) {
          const firstPos = openPositions[0];

          // Если первый лот целиком "закрывается" продажей
          if (firstPos.quantity <= remainToSell) {
            remainToSell -= firstPos.quantity;
            // Удаляем лот из списка
            openPositions.shift();
          } else {
            // Продаём часть лота
            firstPos.quantity -= remainToSell;
            remainToSell = 0;
          }
        }
      }
    }

    // Подсчитаем, сколько всего бумаг осталось и какова их суммарная стоимость
    let totalQty = 0;
    let totalCost = 0;

    for (const pos of openPositions) {
      totalQty += pos.quantity;
      totalCost += pos.quantity * pos.costPerShare;
    }

    // Средняя цена покупки = Общая стоимость / Количество
    return totalQty > 0 ? totalCost / totalQty : 0;
  }

  /**
   * Возвращает текущую рыночную стоимость всех оставшихся бумаг
   * = (остаток бумаг) * (текущая цена)
   */
  private getMarketValue(currentPrice: number, balanceQty: number): number {
    return balanceQty * currentPrice; // 10 * 3717 = 37170
  }

  /**
   * Абсолютная прибыль (или убыток) в рублях
   */
  private getProfit(operations: Operation[], currentPrice: number, balanceQty: number): number {
    const avgPrice = this.getAveragePrice(operations); // 1324.5
    const costBasis = avgPrice * balanceQty;    // 13245
    const marketValue = currentPrice * balanceQty; // 37170
    return marketValue - costBasis;      // 23925
  }

  /**
   * Доходность в процентах
   */
  private getProfitPercentage(operations: Operation[], currentPrice: number, balanceQty: number): number {
    const profit = this.getProfit(operations, currentPrice, balanceQty); // 23925
    // Себестоимость (сколько потрачено на покупку)
    const avgPrice = this.getAveragePrice(operations); // 1324.5
    const costBasis = avgPrice * balanceQty; // 13245

    // (прибыль / себестоимость) * 100%
    return (profit / costBasis) * 100;
  }

  protected readonly Infinity = Infinity;
}
