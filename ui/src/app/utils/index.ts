import { Quotation } from '../types';

export const getPriceByCandle = (candle: Quotation): number | null => {
  const high = getPriceByQuotation(candle.high);
  const low = getPriceByQuotation(candle.low);

  return (high || low)
    ? (((high ?? 0) + (low ?? 0)) / 2)
    : null;
}

export const getPriceByQuotation = (price: Quotation, isAbsolute = false): number | null => {
  try {
    if (!price?.units && !price?.nano) {
      return null;
    }

    const result = (price.units + Math.round(price.nano / 10000000) / 100);

    return isAbsolute ? Math.abs(result) : result;
  } catch (e) {
    console.error((e as any)?.message ?? e);
    return null;
  }
}

export const getRoundPrice = (price: number): string | null => {
  try {
    return price.toFixed(2);
  } catch (e) {
    console.error((e as any)?.message ?? e);
    return null;
  }
}
