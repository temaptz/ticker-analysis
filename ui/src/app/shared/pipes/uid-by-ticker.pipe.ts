import { inject, Pipe, PipeTransform } from '@angular/core';
import { map, Observable, of } from 'rxjs';
import { ApiService } from '../services/api.service';
import { Instrument } from '../types';


@Pipe({
  name: 'uidByTicker',
  standalone: true
})
export class UidByTickerPipe implements PipeTransform {

  private apiService = inject(ApiService);

  transform(ticker: string): Observable<string | null> {
    try {
      return this.apiService.getInstrument(undefined, ticker)
        .pipe(
          map((resp: Instrument) => resp?.uid ?? null),
        );
    } catch (e) {
      console.error('Error UidByTickerPipe transform', (e as any)?.message ?? e);
    }

    return of(null);
  }

}
