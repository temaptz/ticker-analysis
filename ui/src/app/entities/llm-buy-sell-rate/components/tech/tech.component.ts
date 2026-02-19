import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { TechRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { TechMiniGraphComponent } from '../tech-mini-graph/tech-mini-graph.component';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';

@Component({
  selector: 'tech',
  imports: [CommonModule, MatTooltip, TechMiniGraphComponent, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './tech.component.html',
  styleUrl: './tech.component.scss'
})
export class TechComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  techColor = GRAPH_COLORS.ta_3_tech;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentTechRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: TechRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
