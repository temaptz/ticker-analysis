import { Injectable, isDevMode } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Fundamentals, InstrumentBrandResponse,
  InstrumentHistoryPrice,
  InstrumentInList,
  InstrumentLastPrice, NewsContentResponse, NewsResponse, Operation,
  Prediction,
  PredictionGraph
} from './types';
import { CandleInterval } from './enums';

@Injectable({
  providedIn: 'root'
})
export class AppService {

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

  getInstrument(uid: string): Observable<InstrumentInList[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentInList[]>(`${this.apiUrl}/instrument`, {params: params});
  }

  getInstrumentLastPrices(uid: string): Observable<InstrumentLastPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentLastPrice[]>(`${this.apiUrl}/instrument/last_prices`, {params: params});
  }

  getInstrumentHistoryPrices(uid: string, days: number, interval: CandleInterval): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('days', days);
    params = params.set('interval', interval);

    return this.http.get<InstrumentHistoryPrice[]>(`${this.apiUrl}/instrument/history_prices`, {params: params});
  }

  getInstrumentConsensusForecast(uid: string): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentHistoryPrice[]>(`${this.apiUrl}/instrument/consensus_forecast`, {params: params});
  }

  getInstrumentHistoryForecasts(uid: string): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentHistoryPrice[]>(`${this.apiUrl}/instrument/history_forecasts`, {params: params});
  }

  getInstrumentFundamentals(assetUid: string): Observable<Fundamentals> {
    let params = new HttpParams();
    params = params.set('asset_uid', assetUid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/fundamental`, {params: params});
  }

  getInstrumentPrediction(uid: string): Observable<Prediction> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/prediction`, {params: params});
  }

  getInstrumentPredictionGraph(uid: string): Observable<PredictionGraph[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<PredictionGraph[]>(`${this.apiUrl}/instrument/prediction/graph`, {params: params});
  }

  getInstrumentBalance(account_name: string, uid: string): Observable<number> {
    let params = new HttpParams();
    params = params.set('account_name', account_name);
    params = params.set('uid', uid);

    return this.http.get<number>(`${this.apiUrl}/instrument/balance`, {params: params});
  }

  getInstrumentOperations(account_name: string, figi: string): Observable<Operation[]> {
    let params = new HttpParams();
    params = params.set('account_name', account_name);
    params = params.set('figi', figi);

    return this.http.get<Operation[]>(`${this.apiUrl}/instrument/operations`, {params: params});
  }

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

  getInstrumentBrand(uid: string): Observable<InstrumentBrandResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentBrandResponse>(`${this.apiUrl}/instrument/brand`, {params: params});
  }

}
