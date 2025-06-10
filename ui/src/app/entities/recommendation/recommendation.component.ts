import {
  input,
  inject,
  resource,
  computed,
  Component,
  ResourceLoaderParams,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, RecommendationResp } from '../../shared/types';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
  selector: 'recommendation',
  imports: [CommonModule, PreloaderComponent],
  providers: [],
  templateUrl: './recommendation.component.html',
  styleUrl: './recommendation.component.scss'
})
export class RecommendationComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  isLong = input<boolean>(false);

  recommendationResource = resource<RecommendationResp, {uid: string, isLong: boolean}>({
    request: () => ({
      uid: this.instrumentUid(),
      isLong: this.isLong(),
    }),
    loader: (params: ResourceLoaderParams<{uid: string, isLong: boolean}>) => firstValueFrom(
      this.apiService.getInstrumentInvestRecommendation(params.request.uid, params.request.isLong),
    )
  });

  isRed = computed(() => this.recommendationResource?.value()?.short?.toLocaleLowerCase()?.includes('прода'));
  isGreen = computed(() => this.recommendationResource?.value()?.short?.toLocaleLowerCase()?.includes('покуп'));

  private apiService = inject(ApiService);

}
