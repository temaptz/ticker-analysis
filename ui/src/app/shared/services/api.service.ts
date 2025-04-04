import { Injectable, isDevMode } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Fundamentals,
  InstrumentBrandResponse,
  InstrumentHistoryPrice,
  InstrumentInList,
  InstrumentLastPrice,
  NewsResponse,
  Operation,
  PredictionResp,
  PredictionGraphResp, InstrumentForecastsHistory, FundamentalsHistory, Instrument
} from '../../types';
import { CandleInterval } from '../../enums';
import { CacheObservable } from '../utils/cache';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = isDevMode()
    ? 'http://localhost:8000'
    : '/api';

  constructor(
    private http: HttpClient,
  ) {}

  @CacheObservable()
  getInstruments(): Observable<InstrumentInList[]> {
    return this.http.get<InstrumentInList[]>(`${this.apiUrl}/instruments`);
  }

  @CacheObservable()
  getInstrument(uid: string): Observable<Instrument[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentInList[]>(`${this.apiUrl}/instrument`, {params: params});
  }

  @CacheObservable()
  getInstrumentLastPrices(uid: string): Observable<InstrumentLastPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentLastPrice[]>(`${this.apiUrl}/instrument/last_prices`, {params: params});
  }

  @CacheObservable()
  getInstrumentPriceByDate(uid: string, date: Date): Observable<number> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date', date.toJSON());

    return this.http.get<number>(`${this.apiUrl}/instrument/price_by_date`, {params: params});
  }

  @CacheObservable()
  getInstrumentHistoryPrices(uid: string, days: number, interval: CandleInterval): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('days', days);
    params = params.set('interval', interval);

    return this.http.get<InstrumentHistoryPrice[]>(`${this.apiUrl}/instrument/history_prices`, {params: params});
  }

  @CacheObservable()
  getInstrumentConsensusForecast(uid: string): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentHistoryPrice[]>(`${this.apiUrl}/instrument/consensus_forecast`, {params: params});
  }

  @CacheObservable()
  getInstrumentHistoryForecasts(uid: string): Observable<InstrumentForecastsHistory[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentForecastsHistory[]>(`${this.apiUrl}/instrument/history_forecasts`, {params: params});
  }

  @CacheObservable()
  getInstrumentFundamentals(assetUid: string): Observable<Fundamentals> {
    let params = new HttpParams();
    params = params.set('asset_uid', assetUid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/fundamentals`, {params: params});
  }

  @CacheObservable()
  getInstrumentFundamentalsHistory(assetUid: string): Observable<FundamentalsHistory[]> {
    let params = new HttpParams();
    params = params.set('asset_uid', assetUid);

    return this.http.get<FundamentalsHistory[]>(`${this.apiUrl}/instrument/fundamentals/history`, {params: params});
  }

  @CacheObservable()
  getInstrumentPrediction(uid: string): Observable<PredictionResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/prediction`, {params: params});
  }

  @CacheObservable()
  getInstrumentPredictionGraph(uid: string, from: Date, to: Date, interval: CandleInterval): Observable<PredictionGraphResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date_from', from.toJSON());
    params = params.set('date_to', to.toJSON());
    params = params.set('interval', interval);

    return this.http.get<PredictionGraphResp>(`${this.apiUrl}/instrument/prediction/graph`, {params: params});
  }

  @CacheObservable()
  getInstrumentBalance(account_name: string, uid: string): Observable<number> {
    let params = new HttpParams();
    params = params.set('account_name', account_name);
    params = params.set('uid', uid);

    return this.http.get<number>(`${this.apiUrl}/instrument/balance`, {params: params});
  }

  @CacheObservable()
  getInstrumentOperations(account_name: string, figi: string): Observable<Operation[]> {
    let params = new HttpParams();
    params = params.set('account_name', account_name);
    params = params.set('figi', figi);

    return this.http.get<Operation[]>(`${this.apiUrl}/instrument/operations`, {params: params});
  }

  @CacheObservable()
  getInstrumentNews(uid: string, startDate: Date, endDate: Date, isWithContent = false): Observable<NewsResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('start_date', startDate.toJSON());
    params = params.set('end_date', endDate.toJSON());
    params = params.set('is_with_content', isWithContent ? 'true' : 'false');

    return this.http.get<NewsResponse>(`${this.apiUrl}/instrument/news`, {params: params});
  }

  @CacheObservable()
  getInstrumentBrand(uid: string): Observable<InstrumentBrandResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentBrandResponse>(`${this.apiUrl}/instrument/brand`, {params: params});
  }

}
