import { inject, Injectable } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { ApiService } from './api.service';


@Injectable({
  providedIn: 'root'
})
export class CurrentPriceService {

  private observablesMap = new Map<string, Observable<number | null>>();

  private _api = inject(ApiService);

  getPriceByUid(uid: string): Observable<number | null> {
    if (!this.observablesMap.has(uid)) {
      this.observablesMap.set(
        uid,
        this._api.getInstrumentLastPrice(uid)
          .pipe(
            shareReplay({ bufferSize: 1, refCount: true }),
          )
      );
    }

    return this.observablesMap.get(uid)!;
  }

}
