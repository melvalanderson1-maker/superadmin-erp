import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Tenant, TenantCreate } from '../models';

@Injectable({ providedIn: 'root' })
export class TenantAdminService {
  constructor(private api: ApiService) {}

  listar() {
    return this.api.get<Tenant[]>('/tenants');
  }

  crear(payload: TenantCreate) {
    return this.api.post<Tenant>('/tenants', payload);
  }

  obtener(id: number) {
    return this.api.get<Tenant>(`/tenants/${id}`);
  }
}