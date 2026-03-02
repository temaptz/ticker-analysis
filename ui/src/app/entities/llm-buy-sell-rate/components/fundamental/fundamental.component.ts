import { Component, inject, input, resource, ResourceLoaderParams, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { WeightsService } from '../../../../shared/services/weights.service';
import { FundamentalRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';

@Component({
  selector: 'fundamental',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent, WeightIndicatorComponent],
  providers: [DecimalPipe],
  templateUrl: './fundamental.component.html',
  styleUrl: './fundamental.component.scss'
})
export class FundamentalComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  private weightsService = inject(WeightsService);
  decimalPipe = inject(DecimalPipe);

  fundamentalColor = GRAPH_COLORS.ta_3_fundamental;

  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'fundamental'));

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentFundamentalRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: FundamentalRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }

  protected readonly GRAPH_COLORS = GRAPH_COLORS;
}
