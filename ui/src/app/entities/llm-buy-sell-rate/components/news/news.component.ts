import { Component, inject, input, resource, ResourceLoaderParams, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { WeightsService } from '../../../../shared/services/weights.service';
import { NewsRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { NewsMiniGraphComponent } from '../news-mini-graph/news-mini-graph.component';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';

@Component({
  selector: 'news',
  imports: [CommonModule, MatTooltip, NewsMiniGraphComponent, VerticalScaleComponent, WeightIndicatorComponent],
  providers: [DecimalPipe],
  templateUrl: './news.component.html',
  styleUrl: './news.component.scss'
})
export class NewsComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  private weightsService = inject(WeightsService);
  decimalPipe = inject(DecimalPipe);

  newsColor = GRAPH_COLORS.news_influence_score;

  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'news'));

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentNewsRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: NewsRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
