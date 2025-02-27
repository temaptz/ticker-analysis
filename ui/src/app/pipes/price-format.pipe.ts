import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'priceFormat',
  standalone: true
})
export class PriceFormatPipe implements PipeTransform {

  transform(value: string): string {
    try {
      return value;
    } catch (e) {
      console.error('Error PriceFormatPipe transform', (e as any)?.message ?? e);

      return value;
    }
  }

}
