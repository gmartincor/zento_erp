# Backups Directory

Este directorio está destinado para backups locales de la base de datos.

## Estructura:
- `database/` - Dumps y backups de PostgreSQL (ignorado por git)
- Los archivos `.sql` son específicos de cada desarrollador

## Uso:
```bash
# Hacer backup local
make backup-local
```

**Nota:** Los archivos de backup no se incluyen en el repositorio por privacidad y tamaño.
