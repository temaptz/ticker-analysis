import { Quotation } from '../shared/types';

export const getPriceByCandle = (candle: Quotation): number | null => {
  const high = getPriceByQuotation(candle.high);
  const low = getPriceByQuotation(candle.low);

  return (high || low)
    ? (((high ?? 0) + (low ?? 0)) / 2)
    : null;
}

export const getPriceByQuotation = (
  price: Quotation,
  isAbsolute = false
): number | null => {
  try {
    if (!price?.units && !price?.nano) {
      return null;
    }

    const resultDirty = (price.units + Math.round(price.nano / 10000000) / 100);
    const result = getRoundPrice(resultDirty);

    return (isAbsolute && result)
      ? Math.abs(result)
      : result;
  } catch (e) {
    console.error((e as any)?.message ?? e);
    return null;
  }
}

export const getRoundPrice = (price: number): number | null => {
  try {
    return parseFloat(price.toFixed(2));
  } catch (e) {
    console.error((e as any)?.message ?? e);
    return null;
  }
}
