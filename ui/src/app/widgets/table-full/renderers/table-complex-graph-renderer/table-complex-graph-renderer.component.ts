import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { ComplexGraphComponent } from '../../../../entities/complex-graph/complex-graph.component';


@Component({
  selector: 'table-complex-graph-renderer',
  templateUrl: 'table-complex-graph-renderer.component.html',
  styleUrls: ['table-complex-graph-renderer.component.scss'],
  imports: [
    NgIf,
    ComplexGraphComponent,
    ReactiveFormsModule,
    FormsModule,
  ]
})
export class TableComplexGraphRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);

  complexGraphHistoryDaysCount = 90

  agInit(params: ICellRendererParams): void {
    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
