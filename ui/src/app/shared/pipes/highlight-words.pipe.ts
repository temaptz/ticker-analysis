import { inject, Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'highlightWords',
  standalone: true
})
export class HighlightWordsPipe implements PipeTransform {

  domSanitizer = inject(DomSanitizer);

  transform(text: string, keywords: string[]): SafeHtml {
    if (!keywords?.length || !text?.length) return text;
    const pattern = new RegExp(`(${keywords.join('|')})`, 'gi');
    return this.domSanitizer.bypassSecurityTrustHtml(text.replace(pattern, '<mark>$1</mark>'));
  }

}
