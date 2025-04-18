import { Injectable, isDevMode } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Fundamentals,
  InstrumentBrandResponse,
  InstrumentHistoryPrice,
  InstrumentInList,
  InstrumentLastPriceResp,
  NewsResponse,
  Operation,
  PredictionResp,
  PredictionGraphResp,
  InstrumentForecastsHistory,
  FundamentalsHistory,
  Instrument, InvestCalc, NewsRateResponse, InstrumentForecastsGraphItem, NewsListRatedResponse,
} from '../../types';
import { CandleInterval } from '../../enums';


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

  getInstruments(): Observable<InstrumentInList[]> {
    return this.http.get<InstrumentInList[]>(`${this.apiUrl}/instruments`);
  }

  getInstrument(uid: string): Observable<Instrument[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentInList[]>(`${this.apiUrl}/instrument`, {params: params});
  }

  getInstrumentLastPrice(uid: string): Observable<InstrumentLastPriceResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentLastPriceResp>(`${this.apiUrl}/instrument/last_price`, {params: params});
  }

  getInstrumentPriceByDate(uid: string, date: Date): Observable<number> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date', date.toJSON());

    return this.http.get<number>(`${this.apiUrl}/instrument/price_by_date`, {params: params});
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

  getInstrumentHistoryForecasts(uid: string): Observable<InstrumentForecastsHistory[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentForecastsHistory[]>(`${this.apiUrl}/instrument/history_forecasts`, {params: params});
  }

  getInstrumentForecastsGraph(uid: string, startDate?: Date, endDate?: Date): Observable<InstrumentForecastsGraphItem[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    if (startDate && endDate) {
      params = params.set('start_date', startDate.toJSON());
      params = params.set('end_date', endDate.toJSON());
    }

    return this.http.get<InstrumentForecastsGraphItem[]>(`${this.apiUrl}/instrument/history_forecasts/graph`, {params: params});
  }

  getInstrumentFundamentals(assetUid: string): Observable<Fundamentals> {
    let params = new HttpParams();
    params = params.set('asset_uid', assetUid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/fundamentals`, {params: params});
  }

  getInstrumentFundamentalsHistory(assetUid: string): Observable<FundamentalsHistory[]> {
    let params = new HttpParams();
    params = params.set('asset_uid', assetUid);

    return this.http.get<FundamentalsHistory[]>(`${this.apiUrl}/instrument/fundamentals/history`, {params: params});
  }

  getInstrumentPrediction(uid: string): Observable<PredictionResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<Fundamentals>(`${this.apiUrl}/instrument/prediction`, {params: params});
  }

  getInstrumentPredictionGraph(uid: string, from: Date, to: Date, interval: CandleInterval): Observable<PredictionGraphResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date_from', from.toJSON());
    params = params.set('date_to', to.toJSON());
    params = params.set('interval', interval);

    return this.http.get<PredictionGraphResp>(`${this.apiUrl}/instrument/prediction/graph`, {params: params});
  }

  getInstrumentOperations(figi: string): Observable<Operation[]> {
    let params = new HttpParams();
    params = params.set('figi', figi);

    return this.http.get<Operation[]>(`${this.apiUrl}/instrument/operations`, {params: params});
  }

  getInvestCalc(uid: string): Observable<InvestCalc> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InvestCalc>(`${this.apiUrl}/instrument/invest_calc`, {params: params});
  }

  getInstrumentNews(uid: string, startDate: Date, endDate: Date, isWithContent = false): Observable<NewsResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('start_date', startDate.toJSON());
    params = params.set('end_date', endDate.toJSON());
    params = params.set('is_with_content', isWithContent ? 'true' : 'false');

    return this.http.get<NewsResponse>(`${this.apiUrl}/instrument/news`, {params: params});
  }

  getInstrumentNewsListRated(uid: string, startDate: Date, endDate: Date, isWithContent = false): Observable<NewsListRatedResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('start_date', startDate.toJSON());
    params = params.set('end_date', endDate.toJSON());

    return this.http.get<NewsListRatedResponse>(`${this.apiUrl}/instrument/news/list_rated`, {params: params});
  }

  getInstrumentNewsRate(uid: string, startDate: Date, endDate: Date): Observable<NewsRateResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('start_date', startDate.toJSON());
    params = params.set('end_date', endDate.toJSON());

    return this.http.get<NewsRateResponse>(`${this.apiUrl}/instrument/news/rates`, {params: params});
  }

  getInstrumentBrand(uid: string): Observable<InstrumentBrandResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentBrandResponse>(`${this.apiUrl}/instrument/brand`, {params: params});
  }

}
