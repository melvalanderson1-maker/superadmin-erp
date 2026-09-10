import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AdminLoginResponse } from '../models';

const TOKEN_KEY = 'superadmin_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private tokenSignal = signal<string | null>(localStorage.getItem(TOKEN_KEY));

  readonly token = computed(() => this.tokenSignal());
  readonly estaLogueado = computed(() => !!this.tokenSignal());

  constructor(private http: HttpClient, private router: Router) {}

  login(correo: string, password: string): Observable<AdminLoginResponse> {
    return this.http
      .post<AdminLoginResponse>(`${environment.apiUrl}/auth/login`, { correo, password })
      .pipe(
        tap((res) => {
          localStorage.setItem(TOKEN_KEY, res.access_token);
          this.tokenSignal.set(res.access_token);
        })
      );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.tokenSignal.set(null);
    this.router.navigate(['/login']);
  }
}