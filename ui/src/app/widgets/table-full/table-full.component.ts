import { Component, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { AgGridAngular } from 'ag-grid-angular';
import { AllCommunityModule, ColDef, ModuleRegistry, CellClickedEvent, GridOptions, GridReadyEvent, GridApi } from 'ag-grid-community';
import { InstrumentInList } from '../../types';
import { ApiService } from '../../shared/services/api.service';
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
import { TablePriceRendererComponent } from './renderers/table-price-renderer/table-price-renderer.component';
import {
  ColumnVisibilitySwitchComponent
} from '../../features/column-visibility-switch/column-visibility-switch.component';

ModuleRegistry.registerModules([AllCommunityModule]);


@Component({
  selector: 'table-full',
  imports: [CommonModule, AgGridAngular, ColumnVisibilitySwitchComponent],
  providers: [],
  templateUrl: './table-full.component.html',
  styleUrl: './table-full.component.scss'
})
export class TableFullComponent implements OnInit {

  instruments = signal<InstrumentInList[]>([]);
  isLoaded = signal<boolean>(false);
  colDefs = signal<ColDef[]>([]);

  gridOptions: GridOptions = {
    defaultColDef: {
      sortable: true,
      resizable: true,
      filter: true,
    }
  };

  private router = inject(Router);
  private appService = inject(ApiService);
  private gridApi?: GridApi;

  constructor() {
    effect(() => {
      this.colDefs.set(this.getColDefs());
    });
  }

  ngOnInit() {
    this.appService.getInstruments()
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.instruments.set(resp.filter((i, index) => index < 1000)));
  }

  onGridReady(params: GridReadyEvent) {
    this.gridApi = params.api;
  }

  handleChangeHiddenFields(resp: {colId: string, isVisible: boolean}): void {
    this.gridApi?.setColumnsVisible([resp.colId], resp.isVisible);
  }

  private getColDefs(): ColDef[] {
    return [
      {
        colId: '0',
        headerName: 'Логотип',
        width: 80,
        cellRenderer: TableLogoRendererComponent,
        onCellClicked: (e: CellClickedEvent) => this.router
          .navigate(['/instrument', e.data.uid]),
      },
      {
        colId: '1',
        field: 'ticker',
        headerName: 'Тикер',
        width: 80,
        onCellClicked: (e: CellClickedEvent) => this.router
          .navigate(['/instrument', e.data.uid]),
      },
      {
        colId: '2',
        field: 'name',
        headerName: 'Название',
        width: 160,
        onCellClicked: (e: CellClickedEvent) => this.router
          .navigate(['/instrument', e.data.uid]),
      },
      {
        colId: '3',
        headerName: 'Фундаментальные показатели',
        cellRenderer: TableFundamentalsRendererComponent,
        autoHeight: true,
        width: 200,
      },
      {
        colId: '4',
        headerName: '5 лет',
        cellRenderer: TableGraphRendererComponent,
        cellRendererParams: {
          days: 365 * 5,
          interval: CandleInterval.CANDLE_INTERVAL_MONTH,
        },
        width: 400,
        autoHeight: true,
      },
      {
        colId: '5',
        headerName: 'Год',
        cellRenderer: TableGraphRendererComponent,
        cellRendererParams: {
          days: 365,
          interval: CandleInterval.CANDLE_INTERVAL_WEEK,
        },
        width: 400,
        autoHeight: true,
      },
      {
        colId: '6',
        headerName: '90 дней + прогнозы',
        cellRenderer: TableComplexGraphRendererComponent,
        width: 600,
        autoHeight: true,
      },
      {
        colId: '7',
        headerName: 'Цена',
        cellRenderer: TablePriceRendererComponent,
        width: 160,
      },
      {
        colId: '8',
        headerName: 'Баланс Основной',
        cellRenderer: TableBalanceRendererComponent,
        cellRendererParams: {
          accountName: 'Основной',
        },
        width: 210,
        autoHeight: true,
      },
      {
        colId: '9',
        headerName: 'Баланс аналитический',
        cellRenderer: TableBalanceRendererComponent,
        cellRendererParams: {
          accountName: 'Аналитический',
        },
        width: 210,
        autoHeight: true,
      },
      {
        colId: '10',
        headerName: 'Прогноз аналитиков',
        cellRenderer: TableForecastsRendererComponent,
        width: 200,
        autoHeight: true,
      },
      {
        colId: '11',
        headerName: 'Прогноз на месяц',
        cellRenderer: TablePredictionsRendererComponent,
        width: 160,
        autoHeight: true,
      },
      {
        colId: '12',
        headerName: 'Новости',
        cellRenderer: TableNewsRendererComponent,
        width: 160,
        autoHeight: true,
      },
    ]
  }

}
