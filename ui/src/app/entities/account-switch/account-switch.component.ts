import { Component, DestroyRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AccountService } from '../../shared/services/account.service';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';


@Component({
  selector: 'account-switch',
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  providers: [],
  templateUrl: './account-switch.component.html',
  styleUrl: './account-switch.component.scss'
})
export class AccountSwitchComponent {

  private _accountService = inject(AccountService);
  private _destroyRef = inject(DestroyRef);

  accounts = this._accountService.accounts;

  userMoneyRub = this._accountService.userMoneyRub;

  form = new FormGroup({
    accountId: new FormControl(this._accountService.selectedAccountId()),
  });

  constructor() {
    this.form.valueChanges.pipe(
      takeUntilDestroyed(this._destroyRef)
    ).subscribe((values) => this._accountService.setSelectedAccount(values.accountId ?? null));
  }

}
