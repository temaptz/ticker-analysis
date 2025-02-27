import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { AgGridAngular } from 'ag-grid-angular';
import { AllCommunityModule, ColDef, ModuleRegistry, CellClickedEvent } from 'ag-grid-community';
import { InstrumentInList } from '../../types';
import { AppService } from '../../app.service';
import { TableLogoRendererComponent } from './renderers/table-logo-renderer/table-logo-renderer.component';
import {
  TableFundamentalsRendererComponent
} from './renderers/table-fundamentals-renderer/table-fundamentals-renderer.component';
import { TableBalanceRendererComponent } from './renderers/table-balance-renderer/table-balance-renderer.component';
import {
  TableComplexGraphRendererComponent
} from './renderers/table-complex-graph-renderer/table-complex-graph-renderer.component';
import {
  TableForecastsRendererComponent
} from './renderers/table-forecasts-renderer/table-forecasts-renderer.component';
import { TableGraphRendererComponent } from './renderers/table-graph-renderer/table-graph-renderer.component';
import { CandleInterval } from '../../enums';
import { TableNewsRendererComponent } from './renderers/table-news-renderer/table-news-renderer.component';
import {
  TablePredictionsRendererComponent
} from './renderers/table-predictions-renderer/table-predictions-renderer.component';
import { Router } from '@angular/router';

ModuleRegistry.registerModules([AllCommunityModule]);


@Component({
  selector: 'table-full',
  imports: [CommonModule, AgGridAngular],
  providers: [],
  templateUrl: './table-full.component.html',
  styleUrl: './table-full.component.scss'
})
export class TableFullComponent implements OnInit {

  instruments = signal<InstrumentInList[]>([]);
  isLoaded = signal<boolean>(false);

  colDefs: ColDef[] = [
    {
      headerName: 'Логотип',
      width: 80,
      cellRenderer: TableLogoRendererComponent,
      onCellClicked: (e: CellClickedEvent) => this.router.navigate(['/instrument', e.data.uid]),
    },
    {
      field: 'ticker',
      headerName: 'Тикер',
      width: 80,
      onCellClicked: (e: CellClickedEvent) => this.router.navigate(['/instrument', e.data.uid]),
    },
    {
      field: 'name',
      headerName: 'Название',
      width: 160,
      onCellClicked: (e: CellClickedEvent) => this.router.navigate(['/instrument', e.data.uid]),
    },
    {
      headerName: 'Фундаментальные показатели',
      cellRenderer: TableFundamentalsRendererComponent,
      autoHeight: true,
      width: 200,
    },
    {
      headerName: '5 лет',
      cellRenderer: TableGraphRendererComponent,
      cellRendererParams: {
        days: 365 * 5,
        interval: CandleInterval.CANDLE_INTERVAL_MONTH,
      },
      width: 300,
      autoHeight: true,
    },
    {
      headerName: 'Год',
      cellRenderer: TableGraphRendererComponent,
      cellRendererParams: {
        days: 365,
        interval: CandleInterval.CANDLE_INTERVAL_WEEK,
      },
      width: 300,
      autoHeight: true,
    },
    {
      headerName: '90 дней + прогнозы',
      cellRenderer: TableComplexGraphRendererComponent,
      width: 300,
      autoHeight: true,
    },
    {
      headerName: 'Цена',
    },
    {
      headerName: 'Баланс Основной',
      cellRenderer: TableBalanceRendererComponent,
      cellRendererParams: {
        accountName: 'Основной',
      },
      width: 210,
      autoHeight: true,
    },
    {
      headerName: 'Баланс аналитический',
      cellRenderer: TableBalanceRendererComponent,
      cellRendererParams: {
        accountName: 'Аналитический',
      },
      width: 210,
      autoHeight: true,
    },
    {
      headerName: 'Прогноз аналитиков',
      cellRenderer: TableForecastsRendererComponent,
      width: 200,
      autoHeight: true,
    },
    {
      headerName: 'Прогноз на месяц',
      cellRenderer: TablePredictionsRendererComponent,
      width: 160,
      autoHeight: true,
    },
    {
      headerName: 'Новости',
      cellRenderer: TableNewsRendererComponent,
      width: 160,
      autoHeight: true,
    },
  ];

  private router = inject(Router);
  private appService = inject(AppService);

  constructor() {}

  ngOnInit() {
    this.appService.getInstruments()
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.instruments.set(resp.filter((i, index) => index < 1000)));
  }

}
