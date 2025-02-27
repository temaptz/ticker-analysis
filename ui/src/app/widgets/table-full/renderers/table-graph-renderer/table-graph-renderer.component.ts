import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { GraphComponent } from '../../../../entities/graph/graph.component';
import { CandleInterval } from '../../../../enums';


@Component({
  selector: 'table-graph-renderer',
  templateUrl: 'table-graph-renderer.component.html',
  styleUrls: ['table-graph-renderer.component.scss'],
  imports: [
    NgIf,
    GraphComponent,
  ]
})
export class TableGraphRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);
  days = signal<number>(365);
  interval = signal<CandleInterval>(CandleInterval.CANDLE_INTERVAL_WEEK);

  agInit(params: ICellRendererParams): void {
    if ('days' in params) {
      this.days.set(params.days as number);
    }

    if ('interval' in params) {
      this.interval.set(params.interval as CandleInterval);
    }

    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
