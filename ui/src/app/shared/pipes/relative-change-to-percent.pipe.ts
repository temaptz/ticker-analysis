import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'relativeChangeToPercent',
  standalone: true
})
export class RelativeChangeToPercentPipe implements PipeTransform {

  transform(value: unknown): string | null {
    try {
      const num = parseFloat(value as string);
      return `${num > 0 ? '+' : '-'}${Math.round((num as number) * 100 * 100) / 100} %`;
    } catch (e) {
      console.error('Error RelativeChangeToPercentPipe transform', (e as any)?.message ?? e);

      return null;
    }
  }

}
