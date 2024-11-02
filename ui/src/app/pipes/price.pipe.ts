import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'price',
  standalone: true
})
export class PricePipe implements PipeTransform {

  transform(value: unknown): unknown {
    try {
      return Math.round((value as number) * 100) / 100;
    } catch (e) {
      console.error('Error CurrencyPipe transform', (e as any)?.message ?? e);

      return value;
    }
  }

}
