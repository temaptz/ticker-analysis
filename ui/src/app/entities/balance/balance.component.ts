import { Component, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize, map, combineLatest } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, Operation } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceByQuotationPipe } from '../../shared/pipes/price-by-quotation.pipe';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { CurrentPriceService } from '../../shared/services/current-price.service';


@Component({
    selector: 'balance',
    imports: [CommonModule, PreloaderComponent, PriceByQuotationPipe, PriceRoundPipe],
    providers: [],
    templateUrl: './balance.component.html',
    styleUrl: './balance.component.scss'
})
export class BalanceComponent {

  accountName = input.required<string>();
  instrumentUid = input.required<InstrumentInList['uid']>();
  instrumentFigi = input.required<InstrumentInList['figi']>();

  isLoaded = signal<boolean>(false);
  balance = signal<number | null>(null);
  operations = signal<Operation[]>([]);
  avgPrice = signal<number | null>(null);
  totalCost = signal<number | null>(null);
  isPlus = signal<boolean>(false);
  percentChange = signal<number | null>(null);
  willEarn = signal<number | null>(null);
  currentPrice = signal<number | null>(null);
  getPriceByQuotation = getPriceByQuotation;

  private apiService = inject(ApiService);
  private currentPriceService = inject(CurrentPriceService);

  constructor() {
    effect(() => combineLatest([
      this.apiService.getInstrumentBalance(this.accountName(), this.instrumentUid()),
      this.currentPriceService.getPriceByUid(this.instrumentUid()),
      this.apiService.getInstrumentOperations(this.accountName(), this.instrumentFigi())
    ])
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(([balance, currentPrice, operations]: [number, number | null, Operation[]]) => {
        this.balance.set(balance);
        this.currentPrice.set(currentPrice);
        this.operations.set(
          operations
            ?.filter(i => ['OPERATION_TYPE_BUY', 'OPERATION_TYPE_SELL'].includes(i.operation_type._name_))
          ?? []
        );
      }));

    effect(() => {
      const balance = this.balance();
      const currentPrice = this.currentPrice() ?? 0;

      let avgPrice = 0;
      let totalCost = 0;

      this.operations()
        ?.filter(i => i.operation_type._name_ === 'OPERATION_TYPE_BUY')
        ?.forEach(i => {
          const c = getPriceByQuotation(i.payment, true);

          if (c) {
            totalCost += c;
          }
        });

      if (balance) {
        avgPrice = totalCost / balance;

        this.avgPrice.set(avgPrice ? avgPrice : null);
        this.totalCost.set(totalCost ? totalCost : null);
        this.isPlus.set(avgPrice < currentPrice);
        this.percentChange.set(Math.round(currentPrice / avgPrice * 100));
        this.willEarn.set(Math.abs((balance * currentPrice) - totalCost));
      }
    });
  }

}
