import { Injectable, isDevMode } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Fundamentals, InstrumentBrandResponse,
  InstrumentHistoryPrice,
  InstrumentInList,
  InstrumentLastPrice, NewsContentResponse, NewsResponse, Operation,
  Prediction,
  PredictionGraph, PredictionResp
} from '../../types';
import { CandleInterval } from '../../enums';
import { CacheObservable } from '../utils/cache';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  predictionPercentByUidMap = new Map<string, number>();

  private apiUrl = isDevMode()
    ? 'http://localhost:8000'
    : '/api';

  constructor(
    private http: HttpClient,
  ) {}

  getInstruments(): Observable<InstrumentInList[]> {
    return this.http.get<InstrumentInList[]>(`${this.apiUrl}/instruments`);
  }

  @CacheObservable()
  getInstrument(uid: string): Observable<InstrumentInList[]> {
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
  getInstrumentHistoryForecasts(uid: string): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentHistoryPrice[]>(`${this.apiUrl}/instrument/history_forecasts`, {params: params});
  }

  @CacheObservable()
  getInstrumentFundamentals(assetUid: string): Observable<Fundamentals> {
    let params = new HttpParams();
    params = params.set('asset_uid', assetUid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/fundamental`, {params: params});
  }

  @CacheObservable()
  getInstrumentPrediction(uid: string): Observable<Prediction> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/prediction`, {params: params});
  }

  @CacheObservable()
  getInstrumentPredictionGraph(uid: string, from: Date, to: Date, interval: CandleInterval): Observable<PredictionResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date_from', from.toJSON());
    params = params.set('date_to', to.toJSON());
    params = params.set('interval', interval);

    return this.http.get<PredictionResp>(`${this.apiUrl}/instrument/prediction/graph`, {params: params});
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
  getInstrumentNews(uid: string, startDate: Date, endDate: Date): Observable<NewsResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('start_date', startDate.toJSON());
    params = params.set('end_date', endDate.toJSON());

    return this.http.get<NewsResponse>(`${this.apiUrl}/instrument/news`, {params: params});
  }

  getInstrumentNewsContent(uid: string, startDate: Date, endDate: Date): Observable<NewsContentResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('start_date', startDate.toJSON());
    params = params.set('end_date', endDate.toJSON());

    return this.http.get<NewsContentResponse>(`${this.apiUrl}/instrument/news_content_rated`, {params: params});
  }

  @CacheObservable()
  getInstrumentBrand(uid: string): Observable<InstrumentBrandResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentBrandResponse>(`${this.apiUrl}/instrument/brand`, {params: params});
  }

}
