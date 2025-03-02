import { Component, effect, inject, Signal, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { BalanceComponent } from '../../../../entities/balance/balance.component';
import { CurrentPriceService } from '../../../../shared/services/current-price.service';


@Component({
  selector: 'table-balance-renderer',
  templateUrl: 'table-balance-renderer.component.html',
  styleUrls: ['table-balance-renderer.component.scss'],
  imports: [
    NgIf,
    BalanceComponent,
  ]
})
export class TableBalanceRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);
  currentPrice = signal<number | null>(null);
  accountName = signal<string | null>(null);

  private currentPriceService = inject(CurrentPriceService);

  constructor() {
    effect(() => {
      const uid = this.instrument()?.uid;

      if (uid) {
        this.currentPriceService.getPriceByUid(uid)
          .subscribe(price => this.currentPrice.set(price))
      }
    });
  }


  agInit(params: ICellRendererParams): void {
    if ('accountName' in params) {
      this.accountName.set(params.accountName as string);
    }

    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
