import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { AccountService } from '../../shared/services/account.service';
import { InstrumentInList, InvestCalc, Operation } from '../../shared/types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceByQuotationPipe } from '../../shared/pipes/price-by-quotation.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { OperationTypeEnum } from '../../shared/enums';


@Component({
  selector: 'balance',
  imports: [CommonModule, PreloaderComponent, PriceByQuotationPipe, PriceFormatPipe],
  providers: [],
  templateUrl: './balance.component.html',
  styleUrl: './balance.component.scss'
})
export class BalanceComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  instrumentFigi = input.required<InstrumentInList['figi']>();
  instrumentLotSize = input.required<InstrumentInList['lot']>();

  isLoaded = signal<boolean>(false);
  operations = signal<Operation[]>([]);
  balanceQty = signal<number | null>(null);
  marketValue = signal<number | null>(null);
  potentialProfit = signal<number | null>(null);
  potentialProfitPercent = signal<number | null>(null);
  avgPrice = signal<number | null>(null);
  currentPrice = signal<number | null>(null);

  protected readonly operationTypeEnum = OperationTypeEnum;
  protected readonly infinity = Infinity;

  private apiService = inject(ApiService);
  private accountService = inject(AccountService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      const accountId = this.accountService.selectedAccountId();
      const instrumentUid = this.instrumentUid();

      this.isLoaded.set(false);

      if (accountId) {
        this.apiService.getInvestCalc(instrumentUid, accountId)
          .pipe(
            takeUntilDestroyed(this.destroyRef),
            finalize(() => this.isLoaded.set(true)),
          )
          .subscribe({
            next: (investCalc: InvestCalc) => {
              if (investCalc?.balance || investCalc?.balance === 0) {
                this.balanceQty.set(investCalc.balance);
              } else {
                this.balanceQty.set(null);
              }

              if (investCalc?.current_price) {
                this.currentPrice.set(investCalc.current_price);
              } else {
                this.currentPrice.set(null);
              }

              if (investCalc?.market_value) {
                this.marketValue.set(investCalc.market_value);
              } else {
                this.marketValue.set(null);
              }

              if (investCalc?.potential_profit) {
                this.potentialProfit.set(investCalc.potential_profit);
              } else {
                this.potentialProfit.set(null);
              }

              if (investCalc?.potential_profit_percent) {
                this.potentialProfitPercent.set(investCalc.potential_profit_percent);
              } else {
                this.potentialProfitPercent.set(null);
              }

              if (investCalc?.avg_price) {
                this.avgPrice.set(investCalc.avg_price);
              } else {
                this.avgPrice.set(null);
              }

              if (investCalc?.operations) {
                this.operations.set(investCalc.operations);
              } else {
                this.operations.set([]);
              }
            },
            error: () => {
              this.balanceQty.set(null);
              this.currentPrice.set(null);
              this.marketValue.set(null);
              this.potentialProfit.set(null);
              this.potentialProfitPercent.set(null);
              this.avgPrice.set(null);
              this.operations.set([]);
            }
          });
      }
    });
  }

}
