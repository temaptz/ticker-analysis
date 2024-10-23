import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { InstrumentHistoryPrice, InstrumentInList, InstrumentLastPrice } from './types';
import { CandleInterval } from './enums';

@Injectable({
  providedIn: 'root'
})
export class AppService {

  constructor(
    private http: HttpClient,
  ) {}

  getInstruments(): Observable<InstrumentInList[]> {
    return this.http.get<InstrumentInList[]>('http://127.0.0.1:8000/instruments');
  }

  getInstrument(uid: string): Observable<InstrumentInList[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentInList[]>('http://127.0.0.1:8000/instrument', {params: params});
  }

  getInstrumentLastPrices(uid: string): Observable<InstrumentLastPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentLastPrice[]>('http://127.0.0.1:8000/instrument/last_prices', {params: params});
  }

  getInstrumentHistoryPrices(uid: string, days: number, interval: CandleInterval): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('days', days);
    params = params.set('interval', interval);

    return this.http.get<InstrumentHistoryPrice[]>('http://127.0.0.1:8000/instrument/history_prices', {params: params});
  }

  getInstrumentConsensusForecast(uid: string): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentHistoryPrice[]>('http://127.0.0.1:8000/instrument/consensus_forecast', {params: params});
  }

  getInstrumentHistoryForecasts(uid: string): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentHistoryPrice[]>('http://127.0.0.1:8000/instrument/history_forecasts', {params: params});
  }

}
