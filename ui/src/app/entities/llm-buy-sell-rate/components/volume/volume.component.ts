import { Component, inject, input, resource, ResourceLoaderParams, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { WeightsService } from '../../../../shared/services/weights.service';
import { VolumeRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';
import { WeightIndicatorComponent } from '../../../../shared/components/weight-indicator/weight-indicator.component';

@Component({
  selector: 'volume',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent, WeightIndicatorComponent],
  templateUrl: './volume.component.html',
  styleUrl: './volume.component.scss'
})
export class VolumeComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  private weightsService = inject(WeightsService);

  volumeColor = GRAPH_COLORS.volume_rate;

  weight = computed(() => this.weightsService.getWeight(this.isBuy(), 'volume'));

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentVolumeRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: VolumeRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }

  prediction = computed<string>(() => (this.rateData.value() as any)?.debug?.['prediction']);

  isPredictionUpper = computed<boolean>(() => this.prediction() === 'upper');
  isPredictionLower = computed<boolean>(() => this.prediction() === 'lower');
  isPredictionSame = computed<boolean>(() => this.prediction() === 'same');

  protected readonly GRAPH_COLORS = GRAPH_COLORS;
}
