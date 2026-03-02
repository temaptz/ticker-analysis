import { Component, inject, input, resource, ResourceLoaderParams, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { WeightsService } from '../../../../shared/services/weights.service';
import { RsiRateResp } from '../../../../shared/types';
import { RsiMiniGraphComponent } from '../rsi-mini-graph/rsi-mini-graph.component';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';

@Component({
  selector: 'rsi',
  imports: [CommonModule, MatTooltip, RsiMiniGraphComponent, VerticalScaleComponent, WeightIndicatorComponent],
  providers: [DecimalPipe],
  templateUrl: './rsi.component.html',
  styleUrl: './rsi.component.scss'
})
export class RsiComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  private weightsService = inject(WeightsService);
  decimalPipe = inject(DecimalPipe);

  rsiColor = GRAPH_COLORS.tech_rsi;

  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'rsi'));

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentRsiRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: RsiRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
