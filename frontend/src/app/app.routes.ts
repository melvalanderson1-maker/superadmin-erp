import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'tenants', pathMatch: 'full' },

  {
    path: 'login',
    loadComponent: () => import('./auth/login/login.component').then((c) => c.LoginComponent),
  },

  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./dashboard/shell/shell.component').then((c) => c.ShellComponent),
    children: [
      {
        path: 'tenants',
        loadComponent: () =>
          import('./dashboard/tenants/tenants-list.component').then((c) => c.TenantsListComponent),
      },
    ],
  },

  { path: '**', redirectTo: '' },
];