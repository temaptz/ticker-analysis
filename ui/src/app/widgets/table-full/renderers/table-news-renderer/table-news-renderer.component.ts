import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams, } from 'ag-grid-community';
import { InstrumentInList } from '../../../../types';
import { NewsComponent } from '../../../../entities/news/news.component';


@Component({
  selector: 'table-news-renderer',
  templateUrl: 'table-news-renderer.component.html',
  styleUrls: ['table-news-renderer.component.scss'],
  imports: [
    NgIf,
    NewsComponent,
  ]
})
export class TableNewsRendererComponent implements ICellRendererAngularComp {

  instrument = signal<InstrumentInList | null>(null);

  agInit(params: ICellRendererParams): void {
    this.refresh(params);
  }

  refresh(params: ICellRendererParams): boolean {
    this.instrument.set(params.data);
    return true;
  }

}
