export interface InstrumentInList {
  uid: string;
  asset_uid: string;
  figi: string;
  ticker: string;
  [key: string]: unknown;
}

export type Instrument = any;
export type InstrumentLastPrice = any;
export type InstrumentHistoryPrice = any;
export type Candle = any;
export type Quotation = any;
export type Forecast = any;
export type Fundamentals = any;
export type Prediction = any;
export type Operation = any;
export type InstrumentBrandResponse = any;

export interface NewsResponse {
  sources: {
    [key: string]: {
      positive_count: number;
      positive_percent: number;
      negative_count: number;
      negative_percent: number;
      neutral_count: number;
      neutral_percent: number;
      total_count: number;
    };
  };
  keywords: string[];
}

export interface NewsContentResponse {
  sources: {
    [key: string]: {
      uid: string;
      title: string;
      text: string;
      date: string;
      rate: number;
    }[];
  };
  keywords: string[];
}

export interface PredictionGraph {
  prediction: number;
  date: string;
}
