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

  guardar(): void {
    if (!this.form.nombre_comercial || !this.form.slug) {
      this.error.set('Completa nombre y slug');
      return;
    }

    this.guardando.set(true);
    this.error.set(null);

    this.tenantService.crear(this.form).subscribe({
      next: () => {
        this.guardando.set(false);
        this.modalAbierto.set(false);
        this.cargarTenants();
      },
      error: (err) => {
        this.guardando.set(false);
        this.error.set(err?.error?.detail ?? 'Error al crear la inmobiliaria');
      },
    });
  }
}