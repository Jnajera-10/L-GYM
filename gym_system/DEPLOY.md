# 🚀 Despliegue en Render GRATIS — Guía Completa

## ⚡ El problema del plan gratuito y la solución

El plan gratuito de Render **duerme el servidor** si no hay visitas por 15 minutos.
Cuando alguien entra después, tarda 15-30 segundos en despertar (cold start).

**Solución GRATIS: UptimeRobot** — pinga tu app cada 5 minutos automáticamente.
Configuración al final de esta guía.

---

## PASO 1 — Instalar Git y subir a GitHub

### Si no tienes Git instalado:
- Windows: https://git-scm.com/download/win
- Mac: ya viene instalado

### Crear repositorio en GitHub:
1. Ve a https://github.com → **"New repository"**
2. Nombre: `gymsystem` → **"Create repository"**

### Subir el código:
Abre una terminal dentro de la carpeta `gym_system/` y ejecuta:

```bash
git init
git add .
git commit -m "GymSystem inicial"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/gymsystem.git
git push -u origin main
```

Cambia `TU_USUARIO` por tu usuario de GitHub.

---

## PASO 2 — Crear cuenta en Render

1. Ve a https://render.com
2. Clic en **"Get Started for Free"**
3. **Regístrate con GitHub** (más fácil, conecta automático)

---

## PASO 3 — Crear la Base de Datos PostgreSQL (GRATIS 90 días)

> Después de 90 días el plan gratuito de DB se elimina.
> Opción: exportar los datos antes y crear una nueva (sigue siendo gratis).
> O usar ElephantSQL/Supabase que son gratuitos permanentes (ver abajo).

1. En Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Configura:
   - **Name:** `gymsystem-db`
   - **Region:** `Ohio (US East)` — más rápido desde Colombia
   - **Plan:** `Free`
3. Clic **"Create Database"** → espera 1-2 minutos
4. Copia la **"Internal Database URL"** → la necesitarás en el Paso 4

### Alternativa GRATIS permanente (recomendada):
Usa **Supabase** (https://supabase.com) — PostgreSQL gratis para siempre.
1. Crea proyecto en Supabase → copia la **Connection String** (modo "Transaction")
2. Úsala como `DATABASE_URL` en el paso siguiente

---

## PASO 4 — Crear el Web Service

1. Dashboard Render → **"New +"** → **"Web Service"**
2. **Connect a repository** → selecciona `gymsystem`
3. Configura así:

| Campo | Valor |
|---|---|
| Name | `gymsystem` |
| Region | `Ohio (US East)` |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:application --workers 1 --threads 4 --worker-class gthread --timeout 120 --bind 0.0.0.0:$PORT` |
| Plan | **Free** |

4. Clic **"Create Web Service"**

---

## PASO 5 — Variables de Entorno

En el Web Service → pestaña **"Environment"** → **"Add Environment Variable"**:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | La URL que copiaste en el Paso 3 |
| `SECRET_KEY` | Genera uno en https://randomkeygen.com (Fort Knox) |
| `FLASK_ENV` | `production` |

Clic **"Save Changes"** → Render redespliega automáticamente.

---

## PASO 6 — Inicializar la base de datos

Cuando el deploy termine (verás **"Live"** en verde):

1. Web Service → pestaña **"Shell"**
2. Escribe:
```bash
python seed.py
```

Verás:
```
✅ Base de datos inicializada.
👤 Usuario: admin | Contraseña: Admin2025!
```

---

## PASO 7 — Entrar al sistema

Tu URL: `https://gymsystem.onrender.com`

- **Usuario:** `admin`
- **Contraseña:** `Admin2025!`
- ⚠️ Cambia la contraseña en Configuración > Usuarios

---

## PASO 8 — Eliminar el cold start (GRATIS con UptimeRobot)

Esto hace que tu app esté siempre activa sin pagar nada.

1. Ve a https://uptimerobot.com → **"Register for FREE"**
2. Dashboard → **"Add New Monitor"**
3. Configura:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `GymSystem`
   - **URL:** `https://gymsystem.onrender.com/health`
   - **Monitoring Interval:** `5 minutes`
4. Clic **"Create Monitor"**

✅ Listo. UptimeRobot pingea tu app cada 5 minutos, Render nunca la duerme.
Además te avisa por email si tu app cae.

---

## PASO 9 — Deploys futuros (automáticos)

Cada vez que actualices el código:

```bash
git add .
git commit -m "descripción del cambio"
git push
```

Render redespliega automáticamente en ~2 minutos.

---

## 🔧 Problemas comunes

**"Application error" al entrar**
→ Ve a Web Service → **"Logs"** y busca el error rojo
→ Asegúrate de haber ejecutado `python seed.py`

**La app tarda 20 segundos en cargar**
→ Normal en el primer acceso (cold start). Configura UptimeRobot (Paso 8).

**Error de base de datos / "no such table"**
→ Ejecuta `python seed.py` desde la Shell de Render

**Build falla con error de pip**
→ Verifica que `requirements.txt` exista y esté bien en GitHub

**"postgres://" error**
→ Ya está corregido en config.py — Render lo convierte a `postgresql://` automáticamente

---

## 📊 Límites del plan gratuito

| Recurso | Límite gratuito |
|---|---|
| Horas de servidor | 750 horas/mes (~25 días) |
| RAM | 512 MB |
| CPU | 0.1 CPU compartida |
| Ancho de banda | 100 GB/mes |
| Base de datos | 90 días gratis |
| Dominios custom | ✅ Incluido |
| HTTPS | ✅ Automático |
| Cold start (sin UptimeRobot) | 15-30 segundos |
| Cold start (con UptimeRobot) | ❌ No existe |

