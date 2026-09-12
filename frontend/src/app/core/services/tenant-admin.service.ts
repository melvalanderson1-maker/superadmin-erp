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

  redeploy(id: number) {
    return this.api.post<Tenant>(`/tenants/${id}/redeploy`, {});
  }

  eliminar(id: number) {
    return this.api.delete<void>(`/tenants/${id}`);
  }

  subirMarca(id: number, tipo: 'logo' | 'mascota' | 'hero', archivo: File) {
    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('tipo', tipo);
    return this.api.post<Tenant>(`/tenants/${id}/marca`, formData);
  }

  actualizarColores(id: number, payload: { color_primario: string; color_secundario: string }) {
    return this.api.patch<Tenant>(`/tenants/${id}/colores`, payload);
  }

  actualizarContacto(id: number, payload: { whatsapp?: string; correo_contacto?: string }) {
    return this.api.patch<Tenant>(`/tenants/${id}/contacto`, payload);
  }
}