import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'priceRound',
  standalone: true
})
export class PriceRoundPipe implements PipeTransform {

  transform(value: unknown): unknown {
    try {
      return Math.round((value as number) * 100) / 100;
    } catch (e) {
      console.error('Error PriceRoundPipe transform', (e as any)?.message ?? e);

      return value;
    }
  }

}
