import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { InstrumentLogoComponent } from '../../../../entities/instrument-logo/instrument-logo.component';


@Component({
  selector: 'table-logo-renderer',
  templateUrl: 'table-logo-renderer.component.html',
  styleUrls: ['table-logo-renderer.component.scss'],
  imports: [
    NgIf,
    InstrumentLogoComponent,
  ]
})
export class TableLogoRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);

  agInit(params: ICellRendererParams): void {
    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
