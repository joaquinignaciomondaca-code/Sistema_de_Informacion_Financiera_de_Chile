import { boolean, integer, jsonb, pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

/** Catálogo de datasets (tablas del mapa relacional) con su esquema y filas. */
export const datasets = pgTable("dataset", {
  id: serial("id").primaryKey(),
  slug: text("slug").notNull().unique(),
  nombre: text("nombre").notNull(),
  industria: text("industria").notNull(),
  circular: text("circular").notNull(),
  archivo: text("archivo").notNull(),
  descripcion: text("descripcion").notNull(),
  columnas: jsonb("columnas").notNull(),
  filas: jsonb("filas").notNull(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

/** Consultas SQL guardadas por el usuario (persistidas, no solo en localStorage). */
export const consultas = pgTable("consulta", {
  id: serial("id").primaryKey(),
  titulo: text("titulo").notNull(),
  sql: text("sql").notNull(),
  industria: text("industria"),
  origen: text("origen").notNull().default("usuario"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

/** Historial de ejecuciones: auditoría de qué se consultó y cuánto demoró. */
export const ejecuciones = pgTable("ejecucion", {
  id: serial("id").primaryKey(),
  sql: text("sql").notNull(),
  datasetSlug: text("dataset_slug"),
  filas: integer("filas").notNull().default(0),
  ms: integer("ms").notNull().default(0),
  ok: boolean("ok").notNull().default(true),
  error: text("error"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});
