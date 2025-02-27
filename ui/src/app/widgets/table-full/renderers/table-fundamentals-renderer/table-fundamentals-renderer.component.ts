import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { FundamentalsComponent } from '../../../../entities/fundamentals/fundamentals.component';


@Component({
  selector: 'table-fundamentals-renderer',
  templateUrl: 'table-fundamentals-renderer.component.html',
  styleUrls: ['table-fundamentals-renderer.component.scss'],
  imports: [
    NgIf,
    FundamentalsComponent,
  ]
})
export class TableFundamentalsRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);

  agInit(params: ICellRendererParams): void {
    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
