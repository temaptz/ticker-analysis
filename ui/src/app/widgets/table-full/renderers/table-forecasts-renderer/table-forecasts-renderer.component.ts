import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { ForecastComponent } from '../../../../entities/forecast/forecast.component';
import { ForecastHistoryComponent } from '../../../../entities/forecast-history/forecast-history.component';


@Component({
  selector: 'table-forecasts-renderer',
  templateUrl: 'table-forecasts-renderer.component.html',
  styleUrls: ['table-forecasts-renderer.component.scss'],
  imports: [
    NgIf,
    ForecastComponent,
    ForecastHistoryComponent,
  ]
})
export class TableForecastsRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);

  agInit(params: ICellRendererParams): void {
    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
