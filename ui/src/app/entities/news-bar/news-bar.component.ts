import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MathRoundPipe } from '../../shared/pipes/math-round.pipe';


@Component({
    selector: 'news-bar',
  imports: [CommonModule, MathRoundPipe],
    providers: [],
    templateUrl: './news-bar.component.html',
    styleUrl: './news-bar.component.scss'
})
export class NewsBarComponent {

  positivePercent = input.required<number>();
  negativePercent = input.required<number>();
  neutralPercent = input.required<number>();

}
