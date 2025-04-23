import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { InstrumentComplexInfoComponent } from '../../widgets/instrument-complex-info/instrument-complex-info.component';
import { NewsListAccordionComponent } from '../../entities/news-list-accordion/news-list-accordion.component';
import { UidByTickerPipe } from '../../shared/pipes/uid-by-ticker.pipe';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';


@Component({
  selector: 'instrument',
  imports: [CommonModule, InstrumentComplexInfoComponent, NewsListAccordionComponent, UidByTickerPipe, PreloaderComponent],
  providers: [],
  templateUrl: './instrument.component.html',
  styleUrl: './instrument.component.scss'
})
export class InstrumentComponent {

  ticker = signal<string>('');

  private activatedRoute = inject(ActivatedRoute);

  constructor() {
    this.ticker.set(
      this.activatedRoute.snapshot.params['ticker']
    );
  }

}
