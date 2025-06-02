import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { GRAPH_COLORS } from '../../shared/const';
import { PredictionResp } from '../../shared/types';
import { ModelNameEnum } from '../../shared/enums';


@Component({
  selector: 'prediction-item',
  imports: [CommonModule, PriceRoundPipe, PriceFormatPipe],
  providers: [],
  templateUrl: './prediction-item.component.html',
  styleUrl: './prediction-item.component.scss'
})
export class PredictionItemComponent {

  predictionResp = input.required<PredictionResp>();
  modelName = input.required<ModelNameEnum>();
  currentPrice = input.required<number>();

  isPlus = computed<boolean>(() => (this.prediction() ?? 0) > (this.currentPrice() ?? 0));

  percent = computed<number>(() => Math.round(Math.abs((this.prediction() ?? 0) - (this.currentPrice() ?? 0)) / (this.currentPrice() ?? 0) * 10000) / 100);

  prediction = computed<number | null>(() => {
    const predictionResp = this.predictionResp();
    const modelName = this.modelName();

    if (modelName && predictionResp?.[modelName]) {
      return predictionResp[modelName];
    }

    return null;
  });

  modelColor = computed<string>(() => {
    switch (this.modelName()) {
      case ModelNameEnum.Ta_1:
        return GRAPH_COLORS.ta_1;
      case ModelNameEnum.Ta_1_1:
        return GRAPH_COLORS.ta_1_1;
      case ModelNameEnum.Ta_1_2:
        return GRAPH_COLORS.ta_1_2;
      case ModelNameEnum.Ta_2:
        return GRAPH_COLORS.ta_2;
      case ModelNameEnum.Ta_2_1:
        return GRAPH_COLORS.ta_2_1;
      default:
        return '';
    }
  });

}
