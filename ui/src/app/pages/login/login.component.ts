import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/services/auth.service';


@Component({
  selector: 'login',
  imports: [CommonModule, ReactiveFormsModule],
  providers: [],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {

  form = new FormGroup({
    login: new FormControl(
      '',
      {
        validators: [
          Validators.required,
        ],
      }
    ),
    password: new FormControl(
      '',
      {
        validators: [
          Validators.required,
        ],
      }
    ),
  });

  private _authService = inject(AuthService);
  private _router = inject(Router);

  handleSubmit(): void {
    this._authService.login(this.form.value.login!, this.form.value.password!)
      .subscribe(() => this._router.navigateByUrl('/dashboard'));
  }

}
