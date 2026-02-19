import { ModelNameEnum, OperationTypeEnum } from '../enums';

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
export type Fundamentals = any;
export type InstrumentBrandResponse = any;

export interface RecommendationResp {
  short: string;
  long: string;
}

export interface TotalInfo {
  news_week_count: number;
  news_week_rated_count: number;
  news_month_count: number;
  news_month_rated_count: number;
  news_total_count: number;
  news_total_rated_count: number;
}

export interface CurrentUser {
  login: string;
  date_create: string;
  token: string;
}

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
    rate_v2: NewsRateV2;
  }[];
  keywords: string[];
  total_absolute: NewsAbsoluteRate;
  total_percent: NewsPercentRate;
  rate_v2: Partial<NewsRateV2>;
  start_date: string | Date;
  end_date: string | Date;
}


export interface NewsRateV2 {
  sentiment: number;
  impact_strength: number;
  mention_focus: number;
  model_name: string;
  pretrain_name: string;
  generation_time_sec: number;
  generation_date: string;
  influence_score: number;
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


export type PredictionResp = {
  [key in  ModelNameEnum]: number;
} & {
  consensus: number;
  relative: {
    [key in  ModelNameEnum]: number;
  } & {
    consensus: number;
  }
}

export type PredictionGraphResp = {
  [key in  ModelNameEnum]: PredictionGraph[];
}

export interface PredictionHistoryGraphResp {
  [key: string]: PredictionGraph[];
}

export interface PredictionGraph {
  prediction_percent: number;
  prediction: number;
  date: string;
  model_name: string;
}

export interface InstrumentForecastsHistory {
  date: string;
  consensus: any;
}

export interface InstrumentForecastsGraphItem {
  date: string;
  consensus: number;
}

export interface NewsGraphItem {
  date: string;
  influence_score: number;
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
  BuyPerspective = 1,
  SellPerspective = 2,
  LastOperation = 3,
  MarketValue = 4,
  BuyVolume = 5,
  SellVolume = 6,
  BuyMacd = 7,
  SellMacd = 8,
  BuyRsi = 9,
  SellRsi = 10,
  BuyTech = 11,
  SellTech = 12,
  BuyNews = 13,
  SellNews = 14,
  BuyFundamental = 15,
  SellFundamental = 16,
  BuyProfit = 17,
  SellProfit = 18,
  BuyTotalRate = 19,
  SellTotalRate = 20,
}

export interface TechAnalysisOptions {
  isShowRSI?: boolean;
  isShowBB?: boolean;
  isShowEMA?: boolean;
  isShowSMA?: boolean;
  isShowMACD?: boolean;
}

export interface Forecast {
  consensus: {
    consensus: Quotation;
    price_change_rel: Quotation;
  };
}

export interface Operation {
  quantity: number;
  price: Quotation;
  payment: Quotation;
  date: string;
  operation_type: OperationTypeEnum;
}

export interface MacdRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface RsiRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface TechRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface NewsRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface FundamentalRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface VolumeRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface ProfitRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface BuySellTotalRateResp {
  rate: number;
  debug: Record<string, any>;
}

export interface BuySellWeights {
  macd: number;
  rsi: number;
  tech: number;
  news: number;
  fundamental: number;
  volume: number;
  profit: number;
}
