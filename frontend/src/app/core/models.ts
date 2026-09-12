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
  mascota_url?: string;
  hero_url?: string;
  id_plan?: number;
  estado: EstadoTenant;
  fecha_vencimiento?: string;
  created_at: string;
  coolify_app_uuid?: string;
  backend_uuid?: string;
  dominio_backend?: string;
  admin_correo_generado?: string;
  admin_password_generada?: string;
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