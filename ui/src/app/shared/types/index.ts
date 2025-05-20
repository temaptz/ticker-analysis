import { ModelNameEnum } from '../enums';

export interface InstrumentInList extends Instrument {}

export interface Instrument {
  uid: string;
  asset_uid: string;
  figi: string;
  ticker: string;
  name: string;
  [key: string]: unknown;
}

export type InstrumentLastPriceResp = number;
export type InstrumentHistoryPrice = any;
export type Candle = any;
export type Quotation = any;
export type Forecast = any;
export type Fundamentals = any;
export type Operation = any;
export type InstrumentBrandResponse = any;

export interface NewsResponse {
  sources: {
    [key: string]: {
      positive_avg_percent: number;
      negative_avg_percent: number;
      neutral_avg_percent: number;
      total_count: number;
      content: {
        uid: string;
        title: string;
        text: string;
        date: string;
        rate?: NewsPercentRate;
      }[]
    };
  };
  keywords: string[];
  total: {
    positive_avg_percent: number;
    negative_avg_percent: number;
    neutral_avg_percent: number;
    total_count: number;
  };
}


export interface NewsListRatedResponse {
  list: {
    news_uid: string;
    date: string;
    title: string;
    text: string;
    source: string;
    rate_absolute: NewsAbsoluteRate;
    rate_percent: NewsPercentRate;
  }[];
  keywords: string[];
  total_absolute: NewsAbsoluteRate;
  total_percent: NewsPercentRate;
}


export interface NewsAbsoluteRate {
  positive_total: number;
  negative_total: number;
  neutral_total: number;
}


export interface NewsPercentRate {
  positive_percent: number;
  negative_percent: number;
  neutral_percent: number;
}


export interface NewsRateResponse {
  yandex_absolute: NewsAbsoluteRate;
  yandex_percent: NewsPercentRate;
  keywords: string[];
  start_date: string | Date;
  end_date: string | Date;
}


export type PredictionResp = {
  [key in  ModelNameEnum]: number;
} & {
  'consensus': number;
}

export type PredictionGraphResp = {
  [key in  ModelNameEnum]: PredictionGraph[];
}

export interface PredictionHistoryGraphResp {
  [key: string]: PredictionGraph[];
}

export interface PredictionGraph {
  prediction: number;
  date: string;
}

export interface InstrumentForecastsHistory {
  date: string;
  consensus: any;
}

export interface InstrumentForecastsGraphItem {
  date: string;
  consensus: number;
}

export interface TechAnalysisResp {
  RSI: TechAnalysisGraphItem[];
  BB: TechAnalysisGraphItem[];
  EMA: TechAnalysisGraphItem[];
  SMA: TechAnalysisGraphItem[];
  MACD: TechAnalysisGraphItem[];
}

export interface TechAnalysisGraphItem {
  date: string;
  signal?: number;
  macd?: number;
  middle_band?: number;
}

export interface FundamentalsHistory {
  date: string;
  fundamentals: any;
}

export interface InvestCalc {
  balance: number,
  current_price: number,
  market_value: number,
  potential_profit: number,
  potential_profit_percent: number,
  avg_price: number,
  operations: Operation[],
}

export enum SortModeEnum {
  Buy = 1,
  Sell = 2,
  Profit = 3,
  MarketValue = 4,
}
