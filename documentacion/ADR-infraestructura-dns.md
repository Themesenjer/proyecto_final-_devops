# Registro de Decisiones de Arquitectura (ADR)
# Infraestructura Base y Resolución del Reto DNS

**Proyecto:** Habit Tracker - Full Stack DevOps  
**Autor:** Pablo Javier Reyes  
**Fecha:** 13 de julio de 2026  
**Estado:** Aprobado / Implementado en Producción

---

# 1. Contexto

Para soportar el ciclo de vida del proyecto **Habit Tracker**, fue necesario implementar una infraestructura base sobre un servidor **VPS con Ubuntu 24.04 LTS**.

La infraestructura debía cumplir los siguientes objetivos:

- Centralizar la administración de contenedores mediante **Portainer**.
- Implementar un **proxy inverso** para administrar el tráfico HTTP/HTTPS.
- Automatizar la generación y renovación de certificados TLS utilizando **Let's Encrypt**.
- Resolver la validación de certificados mediante el reto **DNS-01** con **DuckDNS**, evitando depender del desafío HTTP tradicional.
- Proporcionar una plataforma estable para futuros despliegues de microservicios.

---

# 2. ADR-03: Downgrade Estratégico de Traefik (v3 → v2.11)

## Contexto

Durante la implementación inicial se utilizó **Traefik v3**, pero el contenedor entraba continuamente en un ciclo de reinicio.

Los registros del sistema mostraban el siguiente error:

```text
Docker API version is too old
```

Como consecuencia, Traefik era incapaz de detectar correctamente los contenedores administrados por Docker y el proxy inverso nunca llegaba a inicializarse.

---

## Decisión

Se decidió realizar un **downgrade controlado de Traefik v3 a Traefik v2.11**, descartando la modificación manual de la compatibilidad con la API de Docker.

---

## Justificación

La decisión se tomó por los siguientes motivos:

- Traefik v2.11 posee una negociación automática de la API de Docker mucho más estable.
- La versión v2 cubría el 100 % de las funcionalidades necesarias para el proyecto.
- Se evitó introducir configuraciones experimentales que pudieran afectar la estabilidad del servidor.
- Se priorizó la disponibilidad del entorno frente al uso de la versión más reciente.

---

## Resultado

Después del cambio de versión, Traefik detectó correctamente el Docker Socket y todos los servicios fueron publicados exitosamente.

---

# 3. ADR-04: Implementación del Reto DNS-01 con DuckDNS

## Contexto

El proyecto requería certificados HTTPS administrados automáticamente por Let's Encrypt.

Debido a que el servidor utilizaría varios subdominios y debía evitar configuraciones HTTP temporales, se optó por utilizar el reto **DNS-01**, el cual valida la propiedad del dominio mediante registros TXT en DNS.

---

## Decisión

Se implementó el desafío DNS-01 utilizando la API de DuckDNS.

Los certificados generados por Let's Encrypt serían almacenados en el archivo:

```text
acme.json
```

Este archivo permanecería protegido mediante permisos restrictivos del sistema operativo.

---

## Justificación

La solución ofrece las siguientes ventajas:

- No requiere exponer temporalmente servicios HTTP para validar el dominio.
- Permite emitir certificados para múltiples subdominios.
- Automatiza completamente la renovación de certificados.
- Reduce la superficie de ataque durante el proceso de validación.
- Protege las claves privadas utilizando permisos POSIX (`chmod 600`).

---

## Resultado

Los certificados TLS comenzaron a emitirse y renovarse automáticamente sin intervención manual.

---

# 4. Incidentes Encontrados Durante la Implementación

Durante el despliegue de la infraestructura se identificaron diversos problemas críticos que fueron solucionados antes de poner el sistema en producción.

---

## Incidente 1. Error de API en Traefik

### Síntoma

El proxy inverso permanecía en reinicio constante y no detectaba los contenedores Docker.

### Causa

Traefik v3 presentaba incompatibilidades con la versión de la API Docker disponible en el servidor.

### Solución

Se reemplazó la imagen:

```yaml
traefik:latest
```

por:

```yaml
traefik:v2.11
```

Tras el cambio, el servicio inició correctamente y comenzó a enrutar todas las peticiones.

---

## Incidente 2. Error de autenticación con DuckDNS

### Síntoma

Let's Encrypt no conseguía crear el registro TXT requerido para el reto DNS.

Los registros mostraban la respuesta:

```text
Result (KO)
```

### Causa

Se identificaron dos errores:

1. El token de DuckDNS contenía un carácter adicional.
2. Se enviaba el dominio completo en lugar del nombre del subdominio requerido por la API.

### Solución

Se verificó el token mediante:

```bash
curl
```

Posteriormente se corrigieron las variables del `docker-compose.yml` y se configuraron servidores DNS públicos:

- 8.8.8.8
- 1.1.1.1

Con ello la propagación DNS se realizó correctamente y Let's Encrypt pudo validar el dominio.

---

## Incidente 3. Permisos incorrectos de `acme.json`

### Síntoma

Traefik no podía guardar los certificados SSL.

### Causa

El archivo había sido creado con permisos:

```text
644
```

Traefik rechaza automáticamente este tipo de permisos por motivos de seguridad.

### Solución

Se reinicializó el archivo y posteriormente se asignaron permisos seguros.

```bash
echo "{}" > acme.json
chmod 600 acme.json
```

Después de reiniciar el stack, los certificados fueron almacenados correctamente.

---

## Incidente 4. Expiración del asistente de instalación de Portainer

### Síntoma

Al acceder a Portainer aparecía el mensaje:

```text
Your Portainer instance timed out for security purposes.
```

### Causa

Portainer invalida automáticamente el proceso de configuración inicial si no se crea un usuario administrador durante los primeros minutos posteriores al despliegue.

### Solución

Se reinició el contenedor mediante:

```bash
docker restart portainer
```

Posteriormente se recuperó el token de instalación utilizando:

```bash
docker logs portainer
```

Finalmente se creó el usuario administrador y se completó la configuración inicial.

---

# 5. Impacto de las Decisiones

Las decisiones adoptadas permitieron obtener una infraestructura con las siguientes características:

- Administración centralizada mediante Portainer.
- Proxy inverso estable utilizando Traefik v2.11.
- Certificados HTTPS generados automáticamente.
- Renovación automática de certificados Let's Encrypt.
- Validación mediante DNS-01 sin exponer servicios HTTP.
- Protección de las claves privadas mediante permisos seguros.
- Plataforma preparada para el despliegue continuo de microservicios.

---

# 6. Conclusión

La infraestructura implementada proporciona una base sólida para el proyecto **Habit Tracker**.

La combinación de **Docker**, **Traefik**, **Portainer**, **DuckDNS** y **Let's Encrypt** permitió construir un entorno seguro, automatizado y fácilmente escalable. Asimismo, la resolución de los incidentes identificados durante el despliegue fortaleció la estabilidad del sistema y dejó preparada la plataforma para futuras integraciones y procesos de despliegue continuo (CI/CD), minimizando la necesidad de intervenciones manuales en la administración de la infraestructura.