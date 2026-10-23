<div align="center">

# 16 · Guías de decisión

**Árboles de decisión para elegir el servicio correcto en cada capa**

[⬅ 15 · Arquitecturas](15-arquitecturas-de-referencia.md) · [🏠 Índice](../README.md) · [17 · Catálogo A–Z ➡](17-catalogo-a-z.md)

</div>

> [!TIP]
> Los árboles son puntos de partida. Valida siempre con: requisitos no funcionales (SLO, RPO/RTO, residencia),
> habilidades del equipo, costo total y **pruebas de concepto con carga real**.

---

## Contenido

1. [Cómputo](#1-cómputo)
2. [Datos](#2-datos)
3. [Mensajería](#3-mensajería)
4. [Integración y orquestación](#4-integración-y-orquestación)
5. [Entrada de tráfico y balanceo](#5-entrada-de-tráfico-y-balanceo)
6. [Identidad de cargas de trabajo](#6-identidad-de-cargas-de-trabajo)
7. [Analítica](#7-analítica)
8. [Inteligencia artificial](#8-inteligencia-artificial)
9. [Conectividad híbrida](#9-conectividad-híbrida)
10. [Decisiones que conviene evitar](#10-decisiones-que-conviene-evitar)

---

## 1. Cómputo

```mermaid
flowchart TD
    A{"¿Migras una app existente<br/>sin cambios?"} -->|Sí| B{"¿Es VMware?"}
    B -->|Sí| AVS["Azure VMware Solution"]
    B -->|No| VM["Virtual Machines / VMSS Flexible"]
    A -->|No| C{"¿Código corto disparado<br/>por eventos?"}
    C -->|Sí| FN["Azure Functions<br/>(Flex Consumption)"]
    C -->|No| D{"¿Contenedores?"}
    D -->|No| E{"¿Web/API clásica?"}
    E -->|Sí| APPS["App Service"]
    E -->|No, cálculo masivo| BATCH["Batch / CycleCloud"]
    D -->|Sí| F{"¿Necesitas la API completa<br/>de Kubernetes, operadores o CRD?"}
    F -->|Sí| G{"¿Quieres operar nodos?"}
    G -->|No| AKSA["AKS Automatic"]
    G -->|Sí| AKSS["AKS Standard"]
    F -->|No| H{"¿Tarea aislada y efímera?"}
    H -->|Sí| I{"¿Código no confiable<br/>o agentes de IA?"}
    I -->|Sí| SBX["Container Apps Sandboxes /<br/>Dynamic sessions"]
    I -->|No| ACI["Container Instances /<br/>Container Apps Jobs"]
    H -->|No| ACA["Container Apps<br/>(+ Dapr)"]
```

| Si además necesitas… | Ajusta la elección |
|---|---|
| OpenShift corporativo | Azure Red Hat OpenShift |
| Spring Boot gestionado | Container Apps con componentes Java (Spring Apps se retira en 2028) |
| Windows Server sin contenedores | VM o App Service (Windows) |
| GPU con escala a cero | Container Apps (GPU *serverless*) |
| Entrenamiento distribuido a gran escala | AKS / ND-series / Azure ML |

---

## 2. Datos

```mermaid
flowchart TD
    A{"¿Qué forma tienen los datos?"} -->|"Relacional / ACID"| B{"¿Motor?"}
    B -->|"SQL Server"| C{"¿Compatibilidad total<br/>con instancia (Agent, CLR)?"}
    C -->|Sí| MI["Azure SQL Managed Instance"]
    C -->|No| SQLDB["Azure SQL Database<br/>(Hyperscale si > 4 TB o crecimiento rápido)"]
    B -->|"PostgreSQL"| PG{"¿Escala horizontal?"}
    PG -->|Sí| PGE["PostgreSQL elastic clusters /<br/>HorizonDB (preview)"]
    PG -->|No| PGF["PostgreSQL Flexible Server"]
    B -->|"MySQL"| MY["MySQL Flexible Server"]
    B -->|"Oracle"| ORA["Oracle Database@Azure"]
    A -->|"Documentos / clave-valor"| D{"¿Distribución global,<br/>latencia < 10 ms, multi-write?"}
    D -->|Sí| COS["Cosmos DB for NoSQL"]
    D -->|"No, API MongoDB y portabilidad"| DOC["Azure DocumentDB"]
    A -->|"Caché / sesiones"| RED["Azure Managed Redis"]
    A -->|"Archivos y objetos"| E{"¿Acceso?"}
    E -->|"REST / lago"| BLOB["Blob / Data Lake Storage"]
    E -->|"SMB/NFS"| FILES["Azure Files / NetApp Files"]
    E -->|"Paralelo HPC/IA"| LUS["Managed Lustre"]
    A -->|"Series temporales / logs"| ADX["Data Explorer / Eventhouse"]
    A -->|"Búsqueda / vectores"| AIS["Azure AI Search"]
    A -->|"Grafos"| GR["Cosmos DB for Apache Gremlin"]
```

---

## 3. Mensajería

```mermaid
flowchart TD
    A{"¿Qué envías?"} -->|"Comandos de negocio<br/>(no pueden perderse)"| B{"¿Orden, transacciones,<br/>DLQ, duplicados?"}
    B -->|Sí| SB["Service Bus<br/>(Premium en producción crítica)"]
    B -->|"No, cola simple y masiva"| SQ["Storage Queues"]
    A -->|"Notificaciones de que algo pasó"| C{"¿Dispositivos MQTT<br/>o consumo pull?"}
    C -->|Sí| EGN["Event Grid namespaces"]
    C -->|No| EG["Event Grid (topics de sistema/personalizados)"]
    A -->|"Flujo continuo de telemetría"| D{"¿Ecosistema Kafka?"}
    D -->|Sí| EHK["Event Hubs (endpoint Kafka)"]
    D -->|No| EH["Event Hubs"]
    A -->|"Tiempo real a navegadores/apps"| WP["Web PubSub / SignalR"]
    A -->|"Push a móviles"| NH["Notification Hubs"]
```

---

## 4. Integración y orquestación

| Necesidad | Primera opción | Por qué |
|---|---|---|
| Integrar SaaS/ERP con conectores y poco código | **Logic Apps** (Standard) | 1 400+ conectores, B2B, flujos visuales |
| Orquestación con estado en código | **Durable Functions** (Durable Task Scheduler) | Patrones *fan-out*, sagas, procesos largos |
| Workflows portables en microservicios | **Dapr Workflows** (Container Apps/AKS) | Independiente del proveedor |
| Movimiento y transformación de datos | **Data Factory** / Fabric Data Factory | Integration runtimes, *data flows* |
| Exponer y gobernar APIs (y MCP) | **API Management** | Seguridad, cuotas, versionado, portal de desarrolladores |
| Llamar on-premises sin abrir puertos | **Azure Relay** (Hybrid Connections) | Conectividad saliente segura |

---

## 5. Entrada de tráfico y balanceo

| Pregunta | Respuesta → servicio |
|---|---|
| ¿HTTP/S con usuarios globales? | **Front Door** (+ WAF) |
| ¿HTTP/S regional o ingress de AKS? | **Application Gateway v2** / **Application Gateway for Containers** |
| ¿TCP/UDP regional? | **Load Balancer Standard** |
| ¿TCP/UDP entre regiones con IP estable? | **Load Balancer Global tier** |
| ¿*Failover* por DNS para cualquier protocolo? | **Traffic Manager** |
| ¿APIs con políticas, cuotas y suscripciones? | **API Management** detrás de la entrada |

Árbol completo en [06 § Elegir el balanceador correcto](06-redes-y-entrega-global.md#5-elegir-el-balanceador-correcto).

---

## 6. Identidad de cargas de trabajo

```mermaid
flowchart TD
    A{"¿Dónde se ejecuta la carga?"} -->|"En un recurso de Azure"| B{"¿Varios recursos comparten<br/>la identidad o se preaprueba?"}
    B -->|Sí| UAMI["Identidad administrada<br/>asignada por el usuario"]
    B -->|No| SAMI["Identidad administrada<br/>asignada por el sistema"]
    A -->|"En AKS / Kubernetes"| WI["Entra Workload ID<br/>(federación OIDC)"]
    A -->|"GitHub Actions, otra nube, CI/CD"| FED["Federación de identidad de carga<br/>(sin secretos)"]
    A -->|"On-premises sin OIDC"| ARC["Servidor habilitado por Arc<br/>(identidad administrada)"]
    ARC -.->|"si no es posible"| CERT["Service principal con certificado"]
```

---

## 7. Analítica

```mermaid
flowchart TD
    A{"¿Punto de partida?"} -->|"Plataforma nueva, BI y autoservicio"| FAB["Microsoft Fabric"]
    A -->|"Ingeniería de datos/ML avanzada,<br/>Spark abierto, multicloud"| DBX["Azure Databricks<br/>(+ OneLake)"]
    A -->|"Data warehouse existente en Synapse"| SYN["Synapse dedicated SQL<br/>→ plan de migración a Fabric Warehouse"]
    A -->|"Logs/telemetría interactivos"| KQL["Data Explorer / Eventhouse"]
    A -->|"Streaming SQL simple"| ASA["Stream Analytics"]
    A -->|"ETL híbrido"| ADF["Data Factory (self-hosted IR)"]
```

---

## 8. Inteligencia artificial

```mermaid
flowchart TD
    A{"¿Qué necesitas?"} -->|"Capacidad cognitiva lista<br/>(OCR, voz, traducción)"| T["Foundry Tools"]
    A -->|"Generar o razonar con texto,<br/>imagen o audio"| B{"¿Necesita tus datos?"}
    B -->|No| M["Foundry Models (+ model router)"]
    B -->|Sí| C{"¿Solo responder o también actuar?"}
    C -->|"Responder con citas"| RAG["RAG: Foundry IQ / AI Search + Foundry Models"]
    C -->|"Actuar con herramientas"| AG["Foundry Agent Service<br/>(+ MCP vía API Management)"]
    A -->|"Modelo propio (tabular, visión, series)"| ML["Azure Machine Learning"]
    A -->|"Copiloto low-code para el negocio"| CS["Copilot Studio"]
    A -->|"Ejecutar en el dispositivo / desconectado"| FL["Foundry Local"]
```

---

## 9. Conectividad híbrida

| Requisito | VPN Gateway | ExpressRoute | Virtual WAN |
|---|---|---|---|
| Ancho de banda | Hasta decenas de Gbps (agregado) | 50 Mbps–100 Gbps (400 Gbps con Direct) | Escala de *hub* |
| Tráfico por Internet | Sí (cifrado IPsec) | No (privado) | Según conexión |
| Latencia predecible | No | **Sí** | Según conexión |
| Muchas sucursales | Manual | Costoso | **Ideal** (SD-WAN de socios) |
| Tiempo de puesta en marcha | Horas | Semanas (proveedor) | Horas a días |
| Recomendación | Pymes, P2S, respaldo de ExpressRoute | Cargas críticas y volumen alto | Topologías globales |

---

## 10. Decisiones que conviene evitar

| Decisión | Por qué evitarla | Mejor opción |
|---|---|---|
| AKS para una sola API sencilla | Sobrecarga operativa | Container Apps o App Service |
| Cosmos DB con clave de partición de baja cardinalidad | Particiones calientes y `429` | Clave de alta cardinalidad o jerárquica |
| Storage Queues para flujos que requieren orden y DLQ | Falta de garantías | Service Bus con sesiones |
| Event Grid para telemetría masiva continua | No es un log reproducible | Event Hubs |
| Strong consistency por defecto | Costo y latencia | Session y excepciones justificadas |
| Secretos en variables de entorno o pipelines | Riesgo de fuga | Identidades administradas, OIDC, Key Vault |
| Una región sin zonas para producción crítica | Sin tolerancia a fallos de datacenter | Servicios zona-redundantes y plan multirregión |
| Nuevos desarrollos en servicios en retiro | Deuda técnica inmediata | Consulta [18 · Retiros](18-retiros-y-ciclo-de-vida.md) |

---

<div align="center">

[⬅ 15 · Arquitecturas](15-arquitecturas-de-referencia.md) · [🏠 Índice](../README.md) · [17 · Catálogo A–Z ➡](17-catalogo-a-z.md)

</div>
