import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, Router, RouterStateSnapshot } from '@angular/router';
import { catchError, map, tap } from 'rxjs';
import { AuthService } from '../services/auth.service';


export const authGuard: CanActivateFn = (route: ActivatedRouteSnapshot, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const goToLogin = () => router.navigateByUrl('/login');

  return authService.getCurrentUser()
    .pipe(
      catchError(() => goToLogin()),
      map(_ => !!_),
      tap(currentUser => {
        if (!currentUser) {
          goToLogin();
        }
      }),
    );
};
