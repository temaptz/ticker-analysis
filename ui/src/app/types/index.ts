export type InstrumentInList = any;
export type Instrument = any;
export type InstrumentLastPrice = any;
export type InstrumentHistoryPrice = any;
export type Candle = any;
export type Quotation = any;
export type Forecast = any;
export type Fundamentals = any;
export type Prediction = any;
export type Operation = any;
export interface NewsResponse {
  sources: {
    [key: string]: {
      positive: number;
      negative: number;
      neutral: number;
      total: number;
    };
  };
  keywords: string[];
}

export interface PredictionGraph {
  prediction: number;
  date: string;
}
