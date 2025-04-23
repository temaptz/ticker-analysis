import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { InstrumentBrandResponse } from '../../types';
import { ApiService } from '../../shared/services/api.service';


@Component({
    selector: 'instrument-logo',
    imports: [CommonModule],
    providers: [],
    templateUrl: './instrument-logo.component.html',
    styleUrl: './instrument-logo.component.scss'
})
export class InstrumentLogoComponent {

  instrumentUid = input.required<string>();

  logoUrl = signal<InstrumentBrandResponse>(null);

  private apiService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      this.apiService.getInstrumentBrand(this.instrumentUid())
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe((brand) => {
          if (!brand?.logo_name) {
            return;
          }

          const logoBaseName = brand.logo_name;
          const extensionRegexp = /\.([^.]+)$/;
          const logoFileWithoutExtension = logoBaseName?.replace(extensionRegexp, '');
          const logoFileExtension = logoBaseName?.match(extensionRegexp)[0];

          this.logoUrl.set(
            `https://invest-brands.cdn-tinkoff.ru/${logoFileWithoutExtension}x160${logoFileExtension}`
          );
        });
    });
  }

}
