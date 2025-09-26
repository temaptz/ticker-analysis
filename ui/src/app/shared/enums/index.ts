export enum CandleInterval {
  CANDLE_INTERVAL_UNSPECIFIED = 0,
  CANDLE_INTERVAL_1_MIN = 1,
  CANDLE_INTERVAL_2_MIN = 6,
  CANDLE_INTERVAL_3_MIN = 7,
  CANDLE_INTERVAL_5_MIN = 2,
  CANDLE_INTERVAL_10_MIN = 8,
  CANDLE_INTERVAL_15_MIN = 3,
  CANDLE_INTERVAL_30_MIN = 9,
  CANDLE_INTERVAL_HOUR = 4,
  CANDLE_INTERVAL_2_HOUR = 10,
  CANDLE_INTERVAL_4_HOUR = 11,
  CANDLE_INTERVAL_DAY = 5,
  CANDLE_INTERVAL_WEEK = 12,
  CANDLE_INTERVAL_MONTH = 13,
}


export enum ModelNameEnum {
  Ta_1 =  'ta_1',
  Ta_1_1 =  'ta_1_1',
  Ta_1_2 =  'ta_1_2',
  Ta_2 =  'ta_2',
  Ta_2_1 =  'ta_2_1',
  Consensus =  'consensus',
}

export enum OperationTypeEnum {
  Buy = 15,
  Sell = 22,
}
