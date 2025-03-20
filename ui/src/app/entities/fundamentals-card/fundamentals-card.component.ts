import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { Fundamentals } from '../../types';


@Component({
  selector: 'fundamentals-card',
  imports: [CommonModule, PriceFormatPipe, PriceRoundPipe],
  templateUrl: './fundamentals-card.component.html',
  styleUrl: './fundamentals-card.component.scss'
})
export class FundamentalsCardComponent {

  fundamentals = input.required<Fundamentals>();

}
