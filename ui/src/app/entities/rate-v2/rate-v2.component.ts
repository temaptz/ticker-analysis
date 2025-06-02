import { Component, input } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { NewsRateV2 } from '../../shared/types';


@Component({
    selector: 'rate-v2',
    imports: [CommonModule],
    providers: [DecimalPipe],
    templateUrl: './rate-v2.component.html',
    styleUrl: './rate-v2.component.scss'
})
export class RateV2Component {

  rate_v2 = input<Partial<NewsRateV2> | null>(null);

}
