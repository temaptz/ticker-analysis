import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'priceFormat',
  standalone: true
})
export class PriceFormatPipe implements PipeTransform {

  transform(value: string | number | null): string {
    try {
      return value?.toString() ?? '';
    } catch (e) {
      console.error('Error PriceFormatPipe transform', (e as any)?.message ?? e);

      return '';
    }
  }

}
