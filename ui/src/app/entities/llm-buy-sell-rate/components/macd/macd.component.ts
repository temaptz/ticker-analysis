import { Component, inject, input, resource, ResourceLoaderParams, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { WeightsService } from '../../../../shared/services/weights.service';
import { MacdRateResp } from '../../../../shared/types';
import { MacdMiniGraphComponent } from '../macd-mini-graph/macd-mini-graph.component';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';

@Component({
  selector: 'macd',
  imports: [CommonModule, MatTooltip, MacdMiniGraphComponent, VerticalScaleComponent, WeightIndicatorComponent],
  providers: [DecimalPipe],
  templateUrl: './macd.component.html',
  styleUrl: './macd.component.scss'
})
export class MacdComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  private weightsService = inject(WeightsService);
  decimalPipe = inject(DecimalPipe);

  macdColor = GRAPH_COLORS.tech_macd;

  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'macd'));

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentMacdRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: MacdRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
