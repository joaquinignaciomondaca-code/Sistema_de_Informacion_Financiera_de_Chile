CREATE SCHEMA "catalog";
--> statement-breakpoint
CREATE TABLE "catalog"."dataset_columns" (
	"id" serial PRIMARY KEY NOT NULL,
	"dataset_id" integer NOT NULL,
	"ordinal" integer NOT NULL,
	"name" text NOT NULL,
	"data_type" text NOT NULL,
	"description" text DEFAULT '' NOT NULL,
	"is_pk" boolean DEFAULT false NOT NULL,
	"nullable" boolean DEFAULT true NOT NULL,
	"masking" text DEFAULT 'none' NOT NULL,
	"business_tag" text,
	"unit" text
);
--> statement-breakpoint
CREATE TABLE "catalog"."dataset_relations" (
	"id" serial PRIMARY KEY NOT NULL,
	"from_dataset_id" integer NOT NULL,
	"from_column" text NOT NULL,
	"to_dataset_id" integer NOT NULL,
	"to_column" text NOT NULL,
	"relation_type" text DEFAULT 'fk' NOT NULL,
	"cardinality" text DEFAULT 'many-to-one' NOT NULL,
	"evidence" text DEFAULT 'column_metadata' NOT NULL,
	"confidence" numeric DEFAULT '1.0' NOT NULL
);
--> statement-breakpoint
CREATE TABLE "catalog"."datasets" (
	"id" serial PRIMARY KEY NOT NULL,
	"domain_id" integer NOT NULL,
	"source_id" integer,
	"name" text NOT NULL,
	"physical_schema" text DEFAULT 'mart' NOT NULL,
	"physical_table" text NOT NULL,
	"layer" text NOT NULL,
	"grain" text NOT NULL,
	"description" text NOT NULL,
	"owner" text NOT NULL,
	"refresh_cadence" text DEFAULT 'monthly' NOT NULL,
	"freshness_slo_hours" integer DEFAULT 720 NOT NULL,
	"row_count" integer DEFAULT 0 NOT NULL,
	"size_mb" numeric DEFAULT '0' NOT NULL,
	"schema_version" integer DEFAULT 1 NOT NULL,
	"status" text DEFAULT 'live' NOT NULL,
	"access_policy" text DEFAULT 'internal' NOT NULL,
	"model_path" text,
	"tags" text DEFAULT '' NOT NULL,
	"last_materialized_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "datasets_domain_name_uq" UNIQUE("domain_id","name")
);
--> statement-breakpoint
CREATE TABLE "catalog"."domains" (
	"id" serial PRIMARY KEY NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"kind" text NOT NULL,
	"regulator" text NOT NULL,
	"owner_team" text NOT NULL,
	"owner_contact" text NOT NULL,
	"description" text NOT NULL,
	CONSTRAINT "domains_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "catalog"."ingest_runs" (
	"id" serial PRIMARY KEY NOT NULL,
	"dataset_id" integer NOT NULL,
	"started_at" timestamp with time zone NOT NULL,
	"finished_at" timestamp with time zone,
	"status" text NOT NULL,
	"rows_in" integer DEFAULT 0 NOT NULL,
	"rows_out" integer DEFAULT 0 NOT NULL,
	"rows_dropped" integer DEFAULT 0 NOT NULL,
	"watermark" text,
	"commit_sha" text,
	"duration_ms" integer DEFAULT 0 NOT NULL,
	"error_message" text
);
--> statement-breakpoint
CREATE TABLE "catalog"."quality_checks" (
	"id" serial PRIMARY KEY NOT NULL,
	"dataset_id" integer NOT NULL,
	"name" text NOT NULL,
	"kind" text NOT NULL,
	"expression" text DEFAULT '' NOT NULL,
	"passed" boolean NOT NULL,
	"observed_value" numeric,
	"threshold" numeric,
	"severity" text DEFAULT 'warn' NOT NULL,
	"ran_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "catalog"."query_log" (
	"id" serial PRIMARY KEY NOT NULL,
	"actor" text DEFAULT 'anon' NOT NULL,
	"sql_text" text NOT NULL,
	"status" text NOT NULL,
	"engine" text DEFAULT 'postgres' NOT NULL,
	"row_count" integer DEFAULT 0 NOT NULL,
	"duration_ms" integer DEFAULT 0 NOT NULL,
	"cached" boolean DEFAULT false NOT NULL,
	"blocked_by" text,
	"error_message" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "catalog"."saved_queries" (
	"id" serial PRIMARY KEY NOT NULL,
	"slug" text NOT NULL,
	"title" text NOT NULL,
	"sql" text NOT NULL,
	"author" text DEFAULT 'analista' NOT NULL,
	"description" text DEFAULT '' NOT NULL,
	"tags" text DEFAULT '' NOT NULL,
	"dataset_refs" text DEFAULT '' NOT NULL,
	"is_favorite" boolean DEFAULT false NOT NULL,
	"run_count" integer DEFAULT 0 NOT NULL,
	"last_run_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "saved_queries_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "catalog"."sources" (
	"id" serial PRIMARY KEY NOT NULL,
	"domain_id" integer NOT NULL,
	"code" text NOT NULL,
	"title" text NOT NULL,
	"issuer" text NOT NULL,
	"effective_date" date,
	"url" text,
	"mandatory" boolean DEFAULT true NOT NULL
);
--> statement-breakpoint
ALTER TABLE "catalog"."dataset_columns" ADD CONSTRAINT "dataset_columns_dataset_id_datasets_id_fk" FOREIGN KEY ("dataset_id") REFERENCES "catalog"."datasets"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "catalog"."dataset_relations" ADD CONSTRAINT "dataset_relations_from_dataset_id_datasets_id_fk" FOREIGN KEY ("from_dataset_id") REFERENCES "catalog"."datasets"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "catalog"."dataset_relations" ADD CONSTRAINT "dataset_relations_to_dataset_id_datasets_id_fk" FOREIGN KEY ("to_dataset_id") REFERENCES "catalog"."datasets"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "catalog"."datasets" ADD CONSTRAINT "datasets_domain_id_domains_id_fk" FOREIGN KEY ("domain_id") REFERENCES "catalog"."domains"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "catalog"."datasets" ADD CONSTRAINT "datasets_source_id_sources_id_fk" FOREIGN KEY ("source_id") REFERENCES "catalog"."sources"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "catalog"."ingest_runs" ADD CONSTRAINT "ingest_runs_dataset_id_datasets_id_fk" FOREIGN KEY ("dataset_id") REFERENCES "catalog"."datasets"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "catalog"."quality_checks" ADD CONSTRAINT "quality_checks_dataset_id_datasets_id_fk" FOREIGN KEY ("dataset_id") REFERENCES "catalog"."datasets"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "catalog"."sources" ADD CONSTRAINT "sources_domain_id_domains_id_fk" FOREIGN KEY ("domain_id") REFERENCES "catalog"."domains"("id") ON DELETE cascade ON UPDATE no action;