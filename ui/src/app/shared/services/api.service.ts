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
  Instrument,
  InvestCalc,
  InstrumentForecastsGraphItem,
  NewsListRatedResponse,
  TechAnalysisResp,
  PredictionHistoryGraphResp, Forecast, RecommendationResp, NewsGraphItem,
} from '../types';
import { CandleInterval } from '../enums';
import { SortModeEnum } from '../types';


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

  getInstruments(sort: SortModeEnum): Observable<InstrumentInList[]> {
    const params = new HttpParams({
      fromObject: {
        sort
      }
    })
    return this.http.get<InstrumentInList[]>(`${this.apiUrl}/instruments`, {params});
  }

  getInstrument(uid?: string, ticker?: string): Observable<Instrument> {
    let params = new HttpParams();

    if (uid) {
      params = params.set('uid', uid);
    }

    if (ticker) {
      params = params.set('ticker', ticker);
    }

    return this.http.get<Instrument>(`${this.apiUrl}/instrument`, {params: params});
  }

  getInstrumentLastPrice(uid: string): Observable<InstrumentLastPriceResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentLastPriceResp>(`${this.apiUrl}/instrument/last_price`, {params: params});
  }

  getInstrumentHistoryPrices(uid: string, days: number, interval: CandleInterval): Observable<InstrumentHistoryPrice[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('days', days);
    params = params.set('interval', interval);

    return this.http.get<InstrumentHistoryPrice[]>(`${this.apiUrl}/instrument/history_prices`, {params: params});
  }

  getInstrumentForecasts(uid: string): Observable<Forecast> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<Forecast>(`${this.apiUrl}/instrument/forecasts`, {params: params});
  }

  getInstrumentHistoryForecasts(uid: string): Observable<InstrumentForecastsHistory[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentForecastsHistory[]>(`${this.apiUrl}/instrument/history_forecasts`, {params: params});
  }

  getInstrumentForecastsGraph(uid: string, startDate?: Date, endDate?: Date, interval?: CandleInterval): Observable<InstrumentForecastsGraphItem[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    if (startDate && endDate) {
      params = params.set('start_date', startDate.toJSON());
      params = params.set('end_date', endDate.toJSON());
    }

    if (interval) {
      params = params.set('interval', interval.toString());
    }

    return this.http.get<InstrumentForecastsGraphItem[]>(`${this.apiUrl}/instrument/history_forecasts/graph`, {params: params});
  }

  getInstrumentFundamentals(uid: string): Observable<Fundamentals> {
    let params = new HttpParams();
    params = params.set('uid', uid);

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

    return this.http.get<PredictionResp>(`${this.apiUrl}/instrument/prediction`, {params: params});
  }

  getInstrumentPredictionConsensus(uid: string, date: Date): Observable<number> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date', date.toJSON());

    return this.http.get<number>(`${this.apiUrl}/instrument/prediction/consensus`, {params: params});
  }

  getInstrumentPredictionGraph(uid: string, from: Date, to: Date, interval: CandleInterval): Observable<PredictionGraphResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date_from', from.toJSON());
    params = params.set('date_to', to.toJSON());
    params = params.set('interval', interval);

    return this.http.get<PredictionGraphResp>(`${this.apiUrl}/instrument/prediction/graph`, {params: params});
  }

  getInstrumentPredictionHistoryGraph(uid: string, from: Date, to: Date, interval: CandleInterval): Observable<PredictionHistoryGraphResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date_from', from.toJSON());
    params = params.set('date_to', to.toJSON());
    params = params.set('interval', interval);

    return this.http.get<PredictionHistoryGraphResp>(`${this.apiUrl}/instrument/prediction/history_graph`, {params: params});
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

  getInstrumentTechGraph(uid: string, startDate?: Date, endDate?: Date, interval?: CandleInterval): Observable<TechAnalysisResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    if (startDate && endDate) {
      params = params.set('start_date', startDate.toJSON());
      params = params.set('end_date', endDate.toJSON());
    }

    if (interval) {
      params = params.set('interval', interval.toString());
    }

    return this.http.get<TechAnalysisResp>(`${this.apiUrl}/instrument/tech_analysis/graph`, {params: params});
  }

  getInstrumentNewsListRated(uid: string, startDate: Date, endDate: Date, isWithContent = false): Observable<NewsListRatedResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('start_date', startDate.toJSON());
    params = params.set('end_date', endDate.toJSON());

    return this.http.get<NewsListRatedResponse>(`${this.apiUrl}/instrument/news/list_rated`, {params: params});
  }

  getInstrumentNewsGraph(uid: string, from: Date, to: Date, interval: CandleInterval): Observable<NewsGraphItem[]> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('date_from', from.toJSON());
    params = params.set('date_to', to.toJSON());
    params = params.set('interval', interval);

    return this.http.get<NewsGraphItem[]>(`${this.apiUrl}/instrument/news/graph`, {params: params});
  }

  getInstrumentBrand(uid: string): Observable<InstrumentBrandResponse> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    return this.http.get<InstrumentBrandResponse>(`${this.apiUrl}/instrument/brand`, {params: params});
  }

  getInstrumentInvestRecommendation(uid: string, isLong = false): Observable<RecommendationResp> {
    let params = new HttpParams();
    params = params.set('uid', uid);

    if (isLong) {
      params = params.set('is_long', 'true');
    }

    return this.http.get<RecommendationResp>(`${this.apiUrl}/instrument/recommendation`, {params: params});
  }

  getInstrumentTag(uid: string, tagName: string): Observable<string> {
    let params = new HttpParams();
    params = params.set('uid', uid);
    params = params.set('tag_name', tagName);

    return this.http.get<string>(`${this.apiUrl}/instrument/tag`, {params: params});
  }

}
