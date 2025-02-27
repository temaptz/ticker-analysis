import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { AppService } from '../../app.service';
import { InstrumentInList } from '../../types';
import { TableRowComponent } from '../../entities/table-row/table-row.component';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';


@Component({
    selector: 'main',
    imports: [CommonModule, PreloaderComponent, TableRowComponent],
    providers: [],
    templateUrl: './main.component.html',
    styleUrl: './main.component.scss'
})
export class MainComponent implements OnInit {

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

    // @ts-ignore
    window.autoscrollInterval = null;

    // @ts-ignore
    window.autoscroll = () => {
      let scrollX = window.scrollX;
      // @ts-ignore
      window.autoscrollInterval = setInterval(() => {
        window.scrollTo(0, scrollX += 1);
      }, 10);
    }

    // @ts-ignore
    window.stopAutoscroll = () => {
      // @ts-ignore
      clearInterval(window.autoscrollInterval);
    }
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
