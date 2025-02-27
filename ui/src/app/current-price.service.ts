import { Injectable } from '@angular/core';
import { map, Observable, shareReplay } from 'rxjs';
import { parseJSON } from 'date-fns';
import { AppService } from './app.service';
import { InstrumentLastPrice } from './types';
import { getPriceByQuotation } from './utils';

@Injectable({
  providedIn: 'root'
})
export class CurrentPriceService {

  observablesMap = new Map<string, Observable<number | null>>();

  constructor(
    private _api: AppService,
  ) {}

  getPriceByUid(uid: string): Observable<number | null> {
    if (!this.observablesMap.has(uid)) {
      this.observablesMap.set(
        uid,
        this._api.getInstrumentLastPrices(uid)
          .pipe(
            map((resp: InstrumentLastPrice[]): number | null => {
              try {
                const price = resp
                  ?.sort((a, b) => parseJSON(a.time).getTime() - parseJSON(b.time).getTime())
                  ?.[0];

                return getPriceByQuotation(price.price);
              } catch (e) {
                console.error('ERROR GETTING CURRENT PRICE', ((e as any)?.message ?? e));
                return null;
              }
            }),
            shareReplay({ bufferSize: 1, refCount: true }),
          )
      );
    }

    return this.observablesMap.get(uid)!;
  }

}
