# Galicia API

API REST para gestión de aeropuertos, aerolíneas y rutas de vuelo construida con FastAPI, SQLAlchemy y PostgreSQL.

## Instancia en ejecucion:
https://upbeat-unused-lizette.ngrok-free.dev/docs#/

## Requerimientos del Sistema

- **Python**: 3.11 o superior (recomendado 3.12)
- **Docker**
- **Docker Compose**

## Estructura del Proyecto

```
galicia_api/
├── app/
│   ├── models/          # Modelos SQLAlchemy
│   ├── schemas/         # Schemas Pydantic
│   ├── services/        # Lógica de negocio
│   ├── routes/          # Endpoints FastAPI
│   ├── middleware/      # Middleware personalizado
│   ├── config.py        # Configuración
│   ├── database.py      # Conexión a BD
│   └── main.py          # Aplicación FastAPI
├── alembic/             # Migraciones de BD
├── data/                # Archivos de datos (CSV/DAT)
├── tests/               # Tests automatizados
├── docker-compose.yml   # Configuración Docker
├── Dockerfile          # Imagen Docker
├── requirements.txt    # Dependencias Python
├── load_initial_data.py # Script de carga inicial
└── .env                # Variables de entorno
```

## Setup del Proyecto

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd galicia_challenge
```

### 2. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus valores (opcional, los valores por defecto funcionan)
code .env
```

### 3. Preparar datos

Coloca tus archivos de datos en la carpeta `data/`:
- `airports.dat` - Información de aeropuertos
- `airlines.csv` - Información de aerolíneas
- `routes*.csv` - Rutas de vuelo (ej: routes20230101.csv)

**Formato esperado:**

**airports.dat:**
```
IDAirport,NombreAeropuerto,Ciudad,Pais,CodigoAeropuerto,Latitud,Longitud,Altitud,DifUTC,CodigoContinente,TimezoneOlson
```

**airlines.csv:**
```
IDAerolinea,NombreAerolinea,Alias,IATA,ICAO,Callsign,Pais,Activa
```

**routes*.csv:**
```
CodAerolinea|IDAerolinea|AeropuertoOrigen|AeropuertoOrigenID|AeropuertoDestino|AeropuertoDestinoID|OperadoCarrier|Stops|Equipamiento|TicketsVendidos|Lugares|PrecioTicket|KilometrosTotales|Fecha
```

## Carga Inicial de Information

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Iniciar base de datos
docker-compose up db -d

# 2. Esperar a que PostgreSQL esté listo
docker-compose logs db

# 3. Ejecutar migraciones
docker-compose exec api alembic upgrade head

# 4. Cargar datos iniciales
docker-compose exec api python load_initial_data.py
```

### Opción 2: Local (Desarrollo)

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar base de datos con Docker
docker-compose up db -d

# 4. Ejecutar migraciones
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 5. Cargar datos iniciales
python load_initial_data.py
```

## Ejecución de la API

### Con Docker Compose (Recomendado)

```bash
# Iniciar todos los servicios
docker-compose up

# En modo detached (segundo plano)
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Detener servicios
docker-compose down
```

### Desarrollo Local

```bash
# Con entorno virtual activado
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verificar la Instalación

Una vez ejecutándose, verifica que todo funciona:

```bash
# Health check
curl http://localhost:8000/health

# Documentación
curl http://localhost:8000/docs
```

## Endpoints Disponibles

- `GET /` - Información básica de la API
- `GET /health` - Health check
- `GET /docs` - Documentación interactiva (Swagger)
- `POST /airports/import` - Cargar aeropuertos desde archivo
- `GET /routes/most_flown_by_country` - Top 5 rutas por país
- `GET /routes/domestic_high_occupancy_altitude_delta` - Aerolineas consecutivas de alta ocupación
- `GET /airlines/occupancy_average` - Promedio de ocupación por aerolínea
- `GET /airlines/consecutive_high_occupancy_routes` - Aerolineas que volaron dias consecutivos en rutas con alta ocupacion.

## Comandos Útiles

```bash
# Reiniciar solo la API
docker-compose restart api

# Ver logs de la base de datos
docker-compose logs db

# Ejecutar migraciones
docker-compose exec api alembic upgrade head

# Acceder al contenedor de la API
docker-compose exec api bash

# Limpiar todo y empezar de nuevo
docker-compose down -v
docker-compose up --build
```

## Estructura de la Base de Datos

### Tablas Principales

- **airports**: Información de aeropuertos
- **airlines**: Información de aerolíneas
- **routes**: Rutas de vuelo con ocupación
- **audits**: Auditoría de requests

### Relaciones

- `routes.airline_id` → `airlines.id`
- `routes.origin_id` → `airports.id`
- `routes.destination_id` → `airports.id`

## Troubleshooting

### Error de conexión a la base de datos

```bash
# Verificar que PostgreSQL esté ejecutándose
docker-compose ps

# Reiniciar servicios
docker-compose restart db
```

### Error en la carga de datos

```bash
# Verificar que los archivos existen
ls -la data/

# Cargar dump inicial de BD
python load_initial_data.py
```


---

## Tecnologías Utilizadas

- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Alembic** - Migraciones de BD
- **PostgreSQL** - Base de datos
- **Pydantic** - Validación de datos
- **Docker** - Contenedorización
- **Uvicorn** - Servidor ASGI
