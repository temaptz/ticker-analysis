import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'dateDurationDays',
  standalone: true
})
export class DateDurationDaysPipe implements PipeTransform {

  transform(value: Date | string): number | null {
    try {
      const date = new Date(value);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      return Math.round(Math.abs(diff) / (1000 * 60 * 60 * 24));
    } catch (e) {
      console.error('Error DateDurationDaysPipe transform', (e as any)?.message ?? e);

      return null;
    }
  }

}
