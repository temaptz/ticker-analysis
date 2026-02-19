import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { NewsRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { NewsMiniGraphComponent } from '../news/news-mini-graph.component';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';

@Component({
  selector: 'news-rate',
  imports: [CommonModule, MatTooltip, NewsMiniGraphComponent, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './news-rate.component.html',
  styleUrl: './news-rate.component.scss'
})
export class NewsRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  newsColor = GRAPH_COLORS.news_influence_score;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentNewsRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: NewsRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
