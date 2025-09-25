import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'daysCountHuman',
  standalone: true
})
export class DaysCountHumanPipe implements PipeTransform {
  private plural(n: number, forms: [string, string, string]): string {
    const n10 = n % 10;
    const n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return forms[0];
    if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return forms[1];
    return forms[2];
  }

  transform(daysCount: number | null | undefined): string | null {
    try {
      if (daysCount == null) return null;

      const sign = daysCount < 0 ? '-' : '';
      const abs = Math.trunc(Math.abs(daysCount));

      let value: number;
      let forms: [string, string, string];

      if (abs >= 365) {
        value = Math.floor(abs / 365);
        forms = ['год', 'года', 'лет'];
      } else if (abs >= 30) {
        value = Math.floor(abs / 30);
        forms = ['месяц', 'месяца', 'месяцев'];
      } else if (abs >= 7) {
        value = Math.floor(abs / 7);
        forms = ['неделя', 'недели', 'недель'];
      } else {
        value = abs;
        forms = ['день', 'дня', 'дней'];
      }

      return `${sign}${value} ${this.plural(value, forms)}`;
    } catch (e) {
      console.error('Error DaysCountHumanPipe transform', (e as any)?.message ?? e);
      return null;
    }
  }
}
