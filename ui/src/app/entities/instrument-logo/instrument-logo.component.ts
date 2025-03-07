import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
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

  constructor(
    private appService: ApiService,
  ) {
    effect(() => {
      this.appService.getInstrumentBrand(this.instrumentUid())
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
