import { Component, effect, input,  signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { InstrumentInList, Operation } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { finalize, map } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceByQuotationPipe } from '../../pipes/price-by-quotation.pipe';
import { PricePipe } from '../../pipes/price.pipe';


@Component({
  selector: 'balance',
  standalone: true,
  imports: [CommonModule, PreloaderComponent, PriceByQuotationPipe, PricePipe],
  providers: [],
  templateUrl: './balance.component.html',
  styleUrl: './balance.component.scss'
})
export class BalanceComponent {

  accountName = input.required<string>();
  instrumentUid = input.required<InstrumentInList['uid']>();
  instrumentFigi = input.required<InstrumentInList['figi']>();
  currentPrice = input.required<number>();

  isLoadedBalance = signal<boolean>(false);
  isLoadedOperations = signal<boolean>(false);
  balance = signal<number | null>(null);
  operations = signal<Operation[]>([]);
  avgPrice = signal<number | null>(null);
  totalCost = signal<number | null>(null);
  isPlus = signal<boolean>(false);
  percentChange = signal<number | null>(null);
  willEarn = signal<number | null>(null);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: AppService,
  ) {
    effect(() => this.appService.getInstrumentBalance(this.accountName(), this.instrumentUid())
      .pipe(finalize(() => this.isLoadedBalance.set(true)))
      .subscribe((resp: number) => this.balance.set(resp)));

    effect(() => this.appService.getInstrumentOperations(this.accountName(), this.instrumentFigi())
      .pipe(
        map((resp: Operation[]): Operation[] => resp?.filter(i => ['OPERATION_TYPE_BUY', 'OPERATION_TYPE_SELL'].includes(i.operation_type._name_))),
        finalize(() => this.isLoadedOperations.set(true)),
      )
      .subscribe((resp: Operation[]) => this.operations.set(resp)));

    effect(() => {
      const balance = this.balance();
      const currentPrice = this.currentPrice();

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
    }, { allowSignalWrites: true });
  }

}
