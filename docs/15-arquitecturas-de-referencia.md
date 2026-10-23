<div align="center">

# 15 · Arquitecturas de referencia

**Siete planos completos para los sistemas distribuidos más comunes, con decisiones, compromisos y servicios exactos**

[⬅ 14 · Web, móvil y escritorio](14-web-movil-comunicaciones-y-escritorio.md) · [🏠 Índice](../README.md) · [16 · Guías de decisión ➡](16-guias-de-decision.md)

</div>

> [!NOTE]
> Cada arquitectura indica **qué servicio cumple cada rol y por qué**, las decisiones críticas y cómo evoluciona.
> Los colores siguen la convención del atlas: azul = entrada/red, turquesa = cómputo, naranja = mensajería,
> morado = datos, rojo = seguridad, índigo = observabilidad.

---

## Contenido

1. [Aplicación web global activa-activa](#1-aplicación-web-global-activa-activa)
2. [Microservicios en AKS o Container Apps](#2-microservicios-en-aks-o-container-apps)
3. [Big Data y streaming en tiempo real](#3-big-data-y-streaming-en-tiempo-real)
4. [IoT industrial del borde a la nube](#4-iot-industrial-del-borde-a-la-nube)
5. [IA generativa: RAG y agentes](#5-ia-generativa-rag-y-agentes)
6. [Sistema transaccional empresarial](#6-sistema-transaccional-empresarial)
7. [Híbrido y nube soberana](#7-híbrido-y-nube-soberana)
8. [Resumen comparativo](#8-resumen-comparativo)

---

## 1. Aplicación web global activa-activa

**Contexto:** usuarios en varios continentes, objetivo de disponibilidad ≥ 99,99 % y latencia < 100 ms.

```mermaid
flowchart TB
    U(["🌍 Usuarios globales"]) --> AFD{{"Front Door Premium<br/>WAF · caché · latencia"}}
    subgraph S1["Stamp West Europe"]
        A1["Container Apps<br/>(zonas)"] --> R1[("Managed Redis")]
    end
    subgraph S2["Stamp East US 2"]
        A2["Container Apps<br/>(zonas)"] --> R2[("Managed Redis")]
    end
    subgraph S3["Stamp Southeast Asia"]
        A3["Container Apps<br/>(zonas)"] --> R3[("Managed Redis")]
    end
    AFD --> A1 & A2 & A3
    A1 & A2 & A3 --> COS[("Cosmos DB<br/>multi-region writes · Session")]
    AFD --> BLOB[("Blob RA-GZRS<br/>activos estáticos")]
    COS -. "change feed → invalidación de caché" .-> R1 & R2 & R3
    EXT["Entra External ID"] -.-> A1 & A2 & A3
    MON["Application Insights por stamp<br/>+ workspace global"] -.-> S1 & S2 & S3
    classDef edge fill:#0078D4,stroke:#003A6C,color:#fff
    classDef compute fill:#00B7C3,stroke:#006B74,color:#04121a
    classDef data fill:#8764B8,stroke:#4B2E83,color:#fff
    classDef sec fill:#D13438,stroke:#750b1c,color:#fff
    classDef obs fill:#4F6BED,stroke:#26389E,color:#fff
    class AFD edge
    class A1,A2,A3 compute
    class COS,BLOB,R1,R2,R3 data
    class EXT sec
    class MON obs
```

| Rol | Servicio | Por qué |
|---|---|---|
| Entrada global | Front Door Premium | Anycast, WAF administrado, orígenes privados, *failover* en segundos |
| Cómputo | Container Apps (o App Service) por *stamp* | Escala automática, redundancia de zona, despliegue idéntico por IaC |
| Datos | Cosmos DB multi-write, Session | Lecturas y escrituras locales; 99,999 % |
| Caché | Azure Managed Redis por región | Latencia sub-ms; invalidación por *change feed* |
| Identidad de clientes | Entra External ID | CIAM gestionado |
| Activos | Blob RA-GZRS + caché de Front Door | Durabilidad y entrega global |

**Decisiones críticas**
- **Conflictos**: con multi-write, define resolución (LWW por `_ts` o procedimiento) y modela datos para minimizarlos
  (p. ej., carritos por usuario con afinidad regional "suave").
- **Sin afinidad de sesión**: el estado vive en Cosmos DB/Redis, no en la instancia.
- **Residencia**: si hay datos que no pueden salir de una geografía, particiona por región (patrón *geode* parcial).
- **Prueba**: *failover* regional mensual con Chaos Studio y Front Door.

---

## 2. Microservicios en AKS o Container Apps

**Contexto:** decenas de servicios con equipos autónomos, despliegues independientes y dominios bien delimitados.

```mermaid
flowchart LR
    CL(["Clientes"]) --> AFD2{{"Front Door"}} --> APIM2{{"API Management<br/>BFF · cuotas · versiones"}}
    subgraph PLAT["AKS Automatic (o Container Apps) · VNet privada"]
        ORD["Pedidos + Dapr"]
        INV["Inventario + Dapr"]
        PAY["Pagos + Dapr"]
        NOT["Notificaciones + Dapr"]
    end
    APIM2 --> ORD & INV
    ORD -- "comandos" --> SB2[["Service Bus Premium<br/>sesiones · transacciones"]]
    SB2 --> PAY & INV
    ORD -- "eventos de dominio" --> EG2(("Event Grid"))
    EG2 --> NOT
    ORD --> DB1[("Cosmos DB")]
    INV --> DB2[("Azure SQL")]
    PAY --> DB3[("PostgreSQL Flexible")]
    GIT["GitOps (Flux) · Fleet Manager"] -.-> PLAT
    OBS2["Managed Prometheus · Grafana<br/>Application Insights"] -.-> PLAT
    classDef edge fill:#0078D4,stroke:#003A6C,color:#fff
    classDef compute fill:#00B7C3,stroke:#006B74,color:#04121a
    classDef msg fill:#CA5010,stroke:#7A2E06,color:#fff
    classDef data fill:#8764B8,stroke:#4B2E83,color:#fff
    class AFD2,APIM2 edge
    class ORD,INV,PAY,NOT compute
    class SB2,EG2 msg
    class DB1,DB2,DB3 data
```

| Rol | Servicio | Por qué |
|---|---|---|
| Gateway | API Management (v2) | Seguridad, versionado, *rate limiting*, BFF por canal |
| Plataforma | **AKS Automatic** (control, operadores, mesh) o **Container Apps** (velocidad, escala a cero) | Según madurez del equipo de plataforma |
| Comunicación síncrona | Invocación Dapr / gRPC con mTLS | Descubrimiento, reintentos y cifrado sin código extra |
| Comandos | Service Bus Premium | Orden por sesión, DLQ, transacciones |
| Eventos de dominio | Event Grid (o Service Bus topics) | *Fan-out* desacoplado |
| Datos | Base de datos por servicio (*polyglot*) | Autonomía y escalado independiente |
| Entrega | GitHub Actions + GitOps + Fleet Manager | Despliegues por etapas y reversibles |

**Decisiones críticas**: transacciones distribuidas con **sagas** y *outbox*; contratos versionados (AsyncAPI/OpenAPI);
*bulkheads* por *node pool* o *namespace*; trazas W3C extremo a extremo.

---

## 3. Big Data y streaming en tiempo real

**Contexto:** millones de eventos por segundo (clics, transacciones, sensores) con paneles en segundos y analítica
histórica.

```mermaid
flowchart LR
    SRC1["Apps / clics"] --> EH3[["Event Hubs<br/>(Kafka)"]]
    SRC2["OLTP (Azure SQL, Cosmos DB)"] -->|"mirroring"| ONE[("OneLake")]
    SRC3["SaaS / archivos"] -->|"Data Factory"| ONE
    EH3 --> ES["Fabric Eventstream"]
    ES --> EVH[("Eventhouse (KQL)<br/>tiempo real")]
    ES --> BRZ[("Lakehouse bronce")]
    BRZ -->|"Spark"| SLV[("Plata")] -->|"Spark / SQL"| GLD[("Oro")]
    EVH --> RTD["Real-Time Dashboards<br/>+ Activator (alertas)"]
    GLD --> PBI["Power BI · agentes de datos · Fabric IQ"]
    PUR["Purview: catálogo · linaje · DLP"] -.-> ONE
    BRZ & SLV & GLD --- ONE
```

| Rol | Servicio | Alternativa |
|---|---|---|
| Ingesta de streams | Event Hubs (Premium/Dedicated) | IoT Hub, Kafka gestionado por socios |
| Procesamiento en tiempo real | Eventstream + Eventhouse | Stream Analytics, Azure Data Explorer, Spark Structured Streaming |
| Lago | OneLake (Delta) | ADLS Gen2 + Databricks Unity Catalog |
| Transformación | Spark en Fabric | Azure Databricks |
| Servicio | Power BI, agentes de datos | APIs sobre SQL endpoint |
| Gobierno | Purview | Unity Catalog (si usas Databricks) |

**Decisiones críticas**: clave de partición y número de particiones; esquema (Schema Registry); retención y
reprocesamiento (Kappa); costos de capacidad Fabric (F-SKU) frente a consumo.

---

## 4. IoT industrial del borde a la nube

```mermaid
flowchart LR
    subgraph EDGE["Planta · Azure Local + AKS Arc"]
        OPC["Máquinas OPC UA"] --> AIO["IoT Operations<br/>broker MQTT · data flows"]
        AIO --> LOC["Inferencia local<br/>(Foundry Local / KAITO)"]
    end
    AIO -->|"telemetría contextualizada"| EGM(("Event Grid MQTT"))
    AIO --> EH4[["Event Hubs"]]
    EGM --> EH4
    EH4 --> RTI["Fabric RTI / ADX"]
    RTI --> DT2["Digital Twins<br/>modelo de planta"]
    RTI --> ALERT["Activator → Logic Apps<br/>órdenes de mantenimiento"]
    DT2 --> APPX["Apps de operación · agentes"]
    ARC2["Azure Arc: Policy · GitOps · Monitor · Defender for IoT"] -.-> EDGE
```

**Decisiones críticas**: procesar y filtrar en el borde (ancho de banda, latencia, operación desconectada);
identidad de dispositivos (X.509 + DPS + Device Registry); modelo de activos común; segmentación OT/IT con
Defender for IoT; **IoT Central** solo para soluciones existentes (se retira en 2029).

---

## 5. IA generativa: RAG y agentes

```mermaid
flowchart TB
    U5(["Usuarios · Teams · web"]) --> FD5{{"Front Door + WAF"}} --> APP5["App / API (Container Apps)"]
    APP5 --> AGT["Foundry Agent Service<br/>orquestador + agentes especialistas"]
    AGT --> GW5{{"API Management · AI gateway<br/>tokens · caché semántica · MCP · A2A"}}
    GW5 --> MOD5["Foundry Models<br/>PTU + spillover a Global Standard"]
    GW5 --> MCP5["Servidores MCP<br/>(APIs internas)"]
    AGT --> IQ5["Foundry IQ → AI Search<br/>recuperación agéntica"]
    AGT --> MEM[("Cosmos DB<br/>historial + vectores")]
    AGT --> SB5[["Service Bus<br/>tareas largas"]] --> FN5["Functions / ACA Jobs"]
    CS5["Content Safety · Prompt Shields"] -.-> AGT
    ID5["Entra Agent ID · RBAC"] -.-> AGT
    OBS5["App Insights (OTel GenAI) · evaluaciones · Defender for AI"] -.-> AGT
    classDef edge fill:#0078D4,stroke:#003A6C,color:#fff
    classDef compute fill:#00B7C3,stroke:#006B74,color:#04121a
    classDef msg fill:#CA5010,stroke:#7A2E06,color:#fff
    classDef data fill:#8764B8,stroke:#4B2E83,color:#fff
    classDef sec fill:#D13438,stroke:#750b1c,color:#fff
    classDef obs fill:#4F6BED,stroke:#26389E,color:#fff
    class FD5,GW5 edge
    class APP5,AGT,FN5,MOD5,MCP5 compute
    class SB5 msg
    class IQ5,MEM data
    class CS5,ID5 sec
    class OBS5 obs
```

| Rol | Servicio | Nota |
|---|---|---|
| Modelos | Foundry Models | Evalúa varios proveedores; *model router* |
| Orquestación | Foundry Agent Service / Agent Framework | *Hosted agents* para lógica propia |
| Conocimiento | Foundry IQ + AI Search | Híbrida + semántica + permisos |
| Herramientas | MCP detrás de API Management | Gobierno, cuotas y auditoría de herramientas |
| Memoria | Cosmos DB (vector + full-text) | Historial por usuario con TTL |
| Seguridad | Content Safety, Entra Agent ID, Purview | Defensa contra inyección y fuga de datos |
| Calidad | Evaluaciones continuas + trazas | Regresiones detectadas antes de producción |

**Decisiones críticas**: humano en el bucle para acciones con efectos; herramientas idempotentes y con mínimo
privilegio; PTU frente a pago por token según perfil de tráfico; evaluación con datos propios antes de cambiar de
modelo.

---

## 6. Sistema transaccional empresarial

```mermaid
flowchart LR
    U6(["Clientes y sucursales"]) --> AFD6{{"Front Door / Application Gateway WAF"}}
    subgraph P6["Región primaria (3 zonas)"]
        WEB6["App Service Premium v3<br/>zone-redundant"] --> SQLP[("Azure SQL Business Critical<br/>zone-redundant")]
        WEB6 --> SBP[["Service Bus Premium<br/>sesiones · transacciones"]]
        SBP --> WRK["Functions / Logic Apps<br/>integración con ERP"]
        WEB6 --> RED6[("Managed Redis")]
    end
    subgraph D6["Región secundaria"]
        WEB6B["App Service (warm standby)"] --> SQLS[("Réplica geo<br/>failover group")]
        SBS[["Service Bus<br/>geo-réplica"]]
    end
    AFD6 --> WEB6
    AFD6 -.->|"prioridad 2"| WEB6B
    SQLP -. "replicación asíncrona" .-> SQLS
    SBP -. "geo-replication" .-> SBS
```

**Claves**: ACID en Azure SQL para el núcleo; *outbox* para publicar eventos; mensajes con `MessageId` de negocio;
*failover groups* con un *listener* estable; Backup con retención a largo plazo; RPO ≈ segundos y RTO ≈ minutos.

---

## 7. Híbrido y nube soberana

```mermaid
flowchart LR
    subgraph ONP["Datacenter propio / soberano"]
        AL["Azure Local<br/>(conectado o desconectado)"]
        AL --> AKSA["AKS habilitado por Arc"]
        AL --> VMA["VM de Azure Local"]
        AL --> SQLA["SQL Server habilitado por Arc"]
        M365L["Microsoft 365 Local · Foundry Local"]
    end
    subgraph AZR["Azure (región)"]
        HUB7["Hub: Azure Firewall · DNS Private Resolver"]
        GOV["Arc: Policy · Monitor · Defender · Update Manager · Fleet Manager"]
        WL7["Cargas en la nube pública"]
    end
    ONP <-->|"ExpressRoute (MACsec) / VPN"| HUB7
    GOV -.->|"plano de control"| ONP
    HUB7 --- WL7
```

**Claves**: un único modelo de gobierno (ARM + Policy) para nube y local; decide qué cargas requieren operación
desconectada; controles de soberanía (claves en Managed HSM/Cloud HSM, EU Data Boundary, Customer Lockbox).

---

## 8. Resumen comparativo

| Arquitectura | Disponibilidad objetivo | RPO / RTO orientativos | Patrones clave | Costo relativo |
|---|---|---|---|---|
| Web global activa-activa | ≥ 99,99 % | ~0 / segundos | Geode, *deployment stamps*, cache-aside | $$$$ |
| Microservicios | 99,95–99,99 % | Segundos / minutos | Saga, outbox, BFF, *sidecar* | $$$ |
| Big Data y streaming | 99,9–99,95 % | Minutos / horas | Kappa, *medallion* | $$–$$$ |
| IoT industrial | 99,9 % + operación local | Según borde | *Edge filtering*, gemelos digitales | $$ |
| IA generativa | 99,9–99,95 % | Minutos | RAG, agentes, *gatekeeper* | $$–$$$$ (tokens) |
| Transaccional empresarial | 99,99 % | Segundos / minutos | ACID + outbox, *warm standby* | $$$ |
| Híbrido y soberano | Según diseño | Según diseño | Gobierno unificado con Arc | $$–$$$ |

---

<div align="center">

[⬅ 14 · Web, móvil y escritorio](14-web-movil-comunicaciones-y-escritorio.md) · [🏠 Índice](../README.md) · [16 · Guías de decisión ➡](16-guias-de-decision.md)

</div>
