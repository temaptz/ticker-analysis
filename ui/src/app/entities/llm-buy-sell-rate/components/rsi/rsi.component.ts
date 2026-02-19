import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { RsiRateResp } from '../../../../shared/types';
import { RsiMiniGraphComponent } from '../rsi-mini-graph/rsi-mini-graph.component';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';

@Component({
  selector: 'rsi',
  imports: [CommonModule, MatTooltip, RsiMiniGraphComponent, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './rsi.component.html',
  styleUrl: './rsi.component.scss'
})
export class RsiComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  rsiColor = GRAPH_COLORS.tech_rsi;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentRsiRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: RsiRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
