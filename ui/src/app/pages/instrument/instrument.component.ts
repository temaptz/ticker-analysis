import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import {
  InstrumentComplexInfoComponent
} from '../../widgets/instrument-complex-info/instrument-complex-info.component';
import { NewsListAccordionComponent } from '../../entities/news-list-accordion/news-list-accordion.component';


@Component({
    selector: 'instrument',
  imports: [CommonModule, InstrumentComplexInfoComponent, NewsListAccordionComponent],
    providers: [],
    templateUrl: './instrument.component.html',
    styleUrl: './instrument.component.scss'
})
export class InstrumentComponent {

  instrumentUid = signal<string>('');
  dateFrom = startOfDay(subDays(new Date(), 6));
  dateTo = endOfDay(new Date());

  constructor(
    private activatedRoute: ActivatedRoute
  ) {
    this.instrumentUid.set(
      this.activatedRoute.snapshot.params['instrumentUid']
    );
  }

}
