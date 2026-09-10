export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
}

export type EstadoTenant = 'provisionando' | 'activo' | 'suspendido' | 'cancelado' | 'error';

export interface Tenant {
  id: number;
  nombre_comercial: string;
  slug: string;
  dominio: string;
  color_primario: string;
  color_secundario: string;
  logo_url?: string;
  id_plan?: number;
  estado: EstadoTenant;
  fecha_vencimiento?: string;
  created_at: string;
}

export interface TenantCreate {
  nombre_comercial: string;
  slug: string;
  dominio: string;
  color_primario: string;
  color_secundario: string;
  logo_url?: string;
  id_plan?: number;
}