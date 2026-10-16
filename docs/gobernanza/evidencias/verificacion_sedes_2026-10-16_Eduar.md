# Verificación manual del cruce de sedes — 16-10-2026

Revisó: Eduar Caicedo. Detalle fila por fila, con la forma de comprobación y las
fuentes consultadas: `verificacion_sedes_2026-10-16_Eduar.xlsx` (esta misma carpeta).

Se revisó `resultados/sedes_por_universidad.csv` y, en `resultados/tabla_maestra_2023_2024.csv`,
las instituciones que el cruce dejó por fuera.

| Revisión | Filas | Resultado |
|---|---|---|
| Sedes asignadas a alguna de las 34 universidades del PTE | 52 | Las 52 pertenecen a la universidad asignada |
| Instituciones oficiales sin asignar: ¿alguna debería estar en las 34? | 51 | 50 no; 1 con duda (ver abajo) |
| Códigos de Saber Pro sin par en el SNIES: ¿alguno es universidad pública? | 3 | Ninguno; los tres son privados |

## Observaciones

- **Universidad Nacional, sedes 1125, 1126 y 9933.** Se asignaron por la columna IES padre del
  SNIES, no por nombre. El revisor las confirmó, además, con la publicación de la universidad
  (Amazonía, Caribe y La Paz; la fuente está en el Excel).
- **UFPS Ocaña (1210).** Es seccional de la UFPS (IES padre 1209), pero el PTE la financia aparte;
  se mantiene como unidad separada.
- **Unitrópico (2743).** Saber Pro la rotula "no oficial"; el SNIES la registra como oficial.
  Se trata como discrepancia de rótulo de la fuente.
- **UAIIN (9929).** Se asignó por nombre en el SNIES (no tiene evaluados en Saber Pro).
- **Universidad Tecnológica de Pereira (1111).** Saber Pro la rotula "ITP" y el SNIES "UTP";
  el código y el IES padre coinciden. Posible error de rótulo en Saber Pro.
- **Duda, código 4107.** En la tabla maestra el mismo código aparece en el SNIES como "Instituto
  Técnico Agrícola ITA" en 2023 y como "Unidad Técnica para el Desarrollo Profesional - UTEDÉ" en
  2024. La duda es sobre el nombre, no sobre la asignación: es una institución técnica profesional
  y no corresponde a ninguna de las 34 universidades.

## Pendiente

El informe pide que la verificación la hagan dos integrantes. Esta es la primera; falta la segunda.
