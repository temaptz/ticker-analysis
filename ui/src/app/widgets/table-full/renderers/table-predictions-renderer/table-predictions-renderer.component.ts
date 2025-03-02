import { Component, effect, inject, Signal, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { PredictionComponent } from '../../../../entities/prediction/prediction.component';
import { CurrentPriceService } from '../../../../shared/services/current-price.service';
import { toSignal } from '@angular/core/rxjs-interop';


@Component({
  selector: 'table-predictions-renderer',
  templateUrl: 'table-predictions-renderer.component.html',
  styleUrls: ['table-predictions-renderer.component.scss'],
  imports: [
    NgIf,
    PredictionComponent,
  ]
})
export class TablePredictionsRendererComponent implements ICellRendererAngularComp {

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
