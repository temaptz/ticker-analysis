import { Component, OnInit, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AppService } from './app.service';
import { CommonModule } from '@angular/common';
import { InstrumentInList } from './types';
import { TableRowComponent } from './components/table-row/table-row.component';
import { CandleInterval } from './enums';
import { GraphComponent } from './components/graph/graph.component';
import { PreloaderComponent } from './components/preloader/preloader.component';
import { finalize, pipe } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, TableRowComponent, GraphComponent, PreloaderComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {

  instruments = signal<InstrumentInList[]>([]);
  isLoaded = signal<boolean>(false);

  isSortDirectionAsc = true;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstruments()
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.instruments.set(resp.filter((i, index) => index < 1000)));
  }

  handleSortPrediction(): void {
    this.instruments()
      .sort((a: InstrumentInList, b: InstrumentInList) => {
        const aVal = this.appService.predictionPercentByUidMap.get(a.uid);
        const bVal = this.appService.predictionPercentByUidMap.get(b.uid);

        if (aVal || aVal === 0) {
          if (bVal || bVal === 0) {
            return this.isSortDirectionAsc ? (bVal - aVal) : (aVal - bVal);
          }

          return -1;
        } else if (bVal || bVal === 0) {
          return 1;
        }

        return 0;
      });

    this.isSortDirectionAsc = !this.isSortDirectionAsc;
  }
}
