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
      positive_avg_percent: number;
      negative_avg_percent: number;
      neutral_avg_percent: number;
      total_count: number;
      content: {
        uid: string;
        title: string;
        text: string;
        date: string;
        rate: {
          positive_percent: number;
          negative_percent: number;
          neutral_percent: number;
        };
      }[]
    };
  };
  keywords: string[];
}

export interface PredictionResp {
  ta1: PredictionGraph[];
}

export interface PredictionGraph {
  prediction: number;
  date: string;
}
