import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { FundamentalRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';

@Component({
  selector: 'fundamental',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './fundamental.component.html',
  styleUrl: './fundamental.component.scss'
})
export class FundamentalComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  fundamentalColor = GRAPH_COLORS.ta_3_fundamental;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentFundamentalRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: FundamentalRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
