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

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstruments()
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.instruments.set(resp.filter((i, index) => index < 1000)));
  }

    protected readonly candleInterval = CandleInterval;
}
