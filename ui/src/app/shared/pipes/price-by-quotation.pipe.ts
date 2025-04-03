import { Pipe, PipeTransform } from '@angular/core';
import { getPriceByQuotation } from '../../utils';

@Pipe({
  name: 'priceByQuotation',
  standalone: true
})
export class PriceByQuotationPipe implements PipeTransform {

  transform(value: unknown, isAbsolute = false): number | null {
    try {
      return getPriceByQuotation(value, isAbsolute);
    } catch (e) {
      console.error('Error CurrencyPipeByQuotation transform', (e as any)?.message ?? e);

      return null;
    }
  }

}
