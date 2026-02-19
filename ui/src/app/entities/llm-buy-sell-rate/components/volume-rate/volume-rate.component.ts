import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { VolumeRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';

@Component({
  selector: 'volume-rate',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './volume-rate.component.html',
  styleUrl: './volume-rate.component.scss'
})
export class VolumeRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  volumeColor = GRAPH_COLORS.volume_rate;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentVolumeRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: VolumeRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
