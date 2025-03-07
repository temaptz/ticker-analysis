import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'mathRound',
  standalone: true
})
export class MathRoundPipe implements PipeTransform {

  transform(value: number): number {
    try {
      return Math.round(value);
    } catch (e) {
      console.error('Error MathRoundPipe transform', (e as any)?.message ?? e);

      return value;
    }
  }

}
