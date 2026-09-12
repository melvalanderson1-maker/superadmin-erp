import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TenantAdminService } from '../../core/services/tenant-admin.service';
import { Tenant, TenantCreate } from '../../core/models';

@Component({
  selector: 'app-tenants-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './tenants-list.component.html',
  styleUrl: './tenants-list.component.css',
})
export class TenantsListComponent implements OnInit {
  tenants = signal<Tenant[]>([]);
  cargando = signal(true);

  modalAbierto = signal(false);
  guardando = signal(false);
  error = signal<string | null>(null);

  redesplegandoId = signal<number | null>(null);

  form: TenantCreate = {
    nombre_comercial: '',
    slug: '',
    dominio: '',
    color_primario: '#1d4ed8',
    color_secundario: '#0f172a',
  };
  slugTocadoManualmente = false;

  constructor(private tenantService: TenantAdminService) {}

  ngOnInit(): void {
    this.cargarTenants();
  }

  cargarTenants(): void {
    this.cargando.set(true);
    this.tenantService.listar().subscribe({
      next: (res) => {
        this.tenants.set(res);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  abrirNuevo(): void {
    this.form = {
      nombre_comercial: '',
      slug: '',
      dominio: '',
      color_primario: '#1d4ed8',
      color_secundario: '#0f172a',
    };
    this.slugTocadoManualmente = false;
    this.error.set(null);
    this.modalAbierto.set(true);
  }

  cerrarModal(): void {
    this.modalAbierto.set(false);
  }

  onNombreChange(): void {
    if (!this.slugTocadoManualmente) {
      this.form.slug = this.generarSlug(this.form.nombre_comercial);
    }
  }

  onSlugChange(): void {
    this.slugTocadoManualmente = true;
  }

  private generarSlug(texto: string): string {
    return texto
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '');
  }

  tiempoTranscurrido = signal(0);
  private timerReloj: any = null;

  guardar(): void {
    if (!this.form.nombre_comercial || !this.form.slug) {
      this.error.set('Completa nombre y slug');
      return;
    }

    this.guardando.set(true);
    this.error.set(null);
    this.tiempoTranscurrido.set(0);

    this.timerReloj = setInterval(() => {
      this.tiempoTranscurrido.update((s) => s + 1);
    }, 1000);

    this.tenantService.crear(this.form).subscribe({
      next: () => {
        clearInterval(this.timerReloj);
        this.guardando.set(false);
        this.modalAbierto.set(false);
        this.cargarTenants();
      },
      error: (err) => {
        clearInterval(this.timerReloj);
        this.guardando.set(false);
        this.error.set(err?.error?.detail ?? 'Error al crear la inmobiliaria');
      },
    });
  }

  redeploy(tenant: Tenant): void {
    this.redesplegandoId.set(tenant.id);
    this.tenantService.redeploy(tenant.id).subscribe({
      next: () => {
        this.redesplegandoId.set(null);
        this.cargarTenants();
      },
      error: () => this.redesplegandoId.set(null),
    });
  }


  modalEliminarAbierto = signal(false);
  tenantAEliminar = signal<Tenant | null>(null);
  eliminando = signal(false);

  abrirConfirmarEliminar(tenant: Tenant): void {
    this.tenantAEliminar.set(tenant);
    this.modalEliminarAbierto.set(true);
  }

  cerrarConfirmarEliminar(): void {
    this.modalEliminarAbierto.set(false);
    this.tenantAEliminar.set(null);
  }

  confirmarEliminar(): void {
    const tenant = this.tenantAEliminar();
    if (!tenant) return;

    this.eliminando.set(true);
    this.tenantService.eliminar(tenant.id).subscribe({
      next: () => {
        this.eliminando.set(false);
        this.modalEliminarAbierto.set(false);
        this.tenantAEliminar.set(null);
        this.cargarTenants();
      },
      error: () => {
        this.eliminando.set(false);
      },
    });
  }



  modalCredencialesAbierto = signal(false);
    tenantCredenciales = signal<Tenant | null>(null);

    verCredenciales(tenant: Tenant): void {
      this.tenantCredenciales.set(tenant);
      this.modalCredencialesAbierto.set(true);
    }

    cerrarCredenciales(): void {
      this.modalCredencialesAbierto.set(false);
  }

  modalMarcaAbierto = signal(false);
  tenantMarca = signal<Tenant | null>(null);
  subiendoMarca = signal<string | null>(null);
  coloresForm = { color_primario: '#1d4ed8', color_secundario: '#0f172a' };
  guardandoColores = signal(false);
  contactoForm = { whatsapp: '', correo_contacto: '' };
  guardandoContacto = signal(false);

  abrirMarca(tenant: Tenant): void {
    this.tenantMarca.set(tenant);
    this.coloresForm = {
      color_primario: tenant.color_primario,
      color_secundario: tenant.color_secundario,
    };
    this.contactoForm = {
      whatsapp: tenant.whatsapp ?? '',
      correo_contacto: tenant.correo_contacto ?? '',
    };
    this.modalMarcaAbierto.set(true);
  }

  cerrarMarca(): void {
    this.modalMarcaAbierto.set(false);
  }

  onArchivoMarcaSeleccionado(tipo: 'logo' | 'mascota' | 'hero', event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];
    const tenant = this.tenantMarca();
    if (!archivo || !tenant) return;

    this.subiendoMarca.set(tipo);
    this.tenantService.subirMarca(tenant.id, tipo, archivo).subscribe({
      next: (actualizado) => {
        this.tenantMarca.set(actualizado);
        this.subiendoMarca.set(null);
        this.cargarTenants();
      },
      error: () => this.subiendoMarca.set(null),
    });
    input.value = '';
  }

  guardarColores(): void {
    const tenant = this.tenantMarca();
    if (!tenant) return;

    this.guardandoColores.set(true);
    this.tenantService.actualizarColores(tenant.id, this.coloresForm).subscribe({
      next: (actualizado) => {
        this.tenantMarca.set(actualizado);
        this.guardandoColores.set(false);
        this.cargarTenants();
      },
      error: () => this.guardandoColores.set(false),
    });
  }

  guardarContacto(): void {
    const tenant = this.tenantMarca();
    if (!tenant) return;

    this.guardandoContacto.set(true);
    this.tenantService.actualizarContacto(tenant.id, this.contactoForm).subscribe({
      next: (actualizado) => {
        this.tenantMarca.set(actualizado);
        this.guardandoContacto.set(false);
        this.cargarTenants();
      },
      error: () => this.guardandoContacto.set(false),
    });
  }
}