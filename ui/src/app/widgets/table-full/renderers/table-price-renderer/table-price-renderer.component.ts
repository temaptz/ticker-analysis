import { Component, effect, inject, signal } from '@angular/core';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { CurrentPriceService } from '../../../../current-price.service';
import { PriceRoundPipe } from '../../../../pipes/price-round.pipe';
import { PriceFormatPipe } from '../../../../pipes/price-format.pipe';


@Component({
  selector: 'table-price-renderer',
  templateUrl: 'table-price-renderer.component.html',
  styleUrls: ['table-price-renderer.component.scss'],
  imports: [
    PriceRoundPipe,
    PriceFormatPipe
  ]
})
export class TablePriceRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);
  currentPrice = signal<number | null>(null);

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
    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
