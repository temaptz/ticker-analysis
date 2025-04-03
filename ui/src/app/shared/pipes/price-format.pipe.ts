import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'priceFormat',
  standalone: true
})
export class PriceFormatPipe implements PipeTransform {

  transform(
    value: string | number | null,
    decimalsCount = 2,
    isSplitDigits = true,
    isShowCurrency = true,
    isAbsolute = false
  ): string {
    try {
      const absNumber: number = isAbsolute
        ? Math.abs(value as number)
        : value as number;
      const roundNumber: number = this.roundNumber(absNumber, decimalsCount);
      const splitNumber: string = isSplitDigits
        ? this.formatNumberWithSpaces(roundNumber)
        : roundNumber.toString();
      const numberWithCurrency: string = isShowCurrency
        ? `${splitNumber} ₽`
        : splitNumber

      return numberWithCurrency.replace(/ /g, '\u00A0');
    } catch (e) {
      console.error('Error PriceFormatPipe transform', (e as any)?.message ?? e);
    }

    return '';
  }

  private roundNumber(value: number, decimalsCount: number): number {
    const factor = Math.pow(10, decimalsCount);
    return Math.round(value * factor) / factor;
  }

  private formatNumberWithSpaces(value: number): string {
    return value.toLocaleString('ru-RU');
  }

}
