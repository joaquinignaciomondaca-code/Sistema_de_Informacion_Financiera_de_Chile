# Módulo Fondos de Inversión (CMF - Ley Única de Fondos)

## Marco Normativo y Régimen de Información
A diferencia de los Fondos Mutuos (que cuentan con descarga mensual masiva en TXT vía Circular 1333), los **Fondos de Inversión (FI)** chilenos (Ley N° 20.712 - Ley Única de Fondos) reportan su información y carteras mediante:

1. **Estados Financieros IFRS (Circular N° 1.998 / NCG N° 365)**:
   - Envío de información financiera trimestral y anual bajo taxonomía IFRS (archivos XML / PDF vía módulo SEIL de la CMF).
   - Incluye notas explicativas con el inventario de activos, contratos derivados de cobertura y valorización de inversiones.
2. **Sistema de Información de Fondos (NCG N° 532 / Manual de Fondos)**:
   - Reporte periódico estandarizado para fiscalización directa de carteras de inversión (`FONDOS01`).

---

## Estructura del Módulo

```
fi/
└── cartera_inversiones/
    ├── inputs/
    ├── outputs/
    ├── scripts/
    └── README.md
```
