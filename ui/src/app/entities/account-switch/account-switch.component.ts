import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AccountService } from '../../shared/services/account.service';


@Component({
  selector: 'account-switch',
  imports: [CommonModule],
  providers: [],
  templateUrl: './account-switch.component.html',
  styleUrl: './account-switch.component.scss'
})
export class AccountSwitchComponent {

  private _accountService = inject(AccountService);

  accounts = computed(() => this._accountService.accounts.value());
  accountId = computed(() => this._accountService.selectedAccountId());
  userMoneyRub = computed(() => this._accountService.userMoneyRub.value());

  handleChange(event: Event): void {
    const target = event?.target as HTMLSelectElement;
    const accountId = target ? parseInt(target?.value) : null;

    if (accountId) {
      this._accountService.setSelectedAccount(accountId);
    }
  }

}
