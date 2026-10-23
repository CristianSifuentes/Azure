<div align="center">

# 19 · Referencia rápida y glosario

**SLA de referencia · límites clave · comandos esenciales · convenciones de nombres · glosario**

[⬅ 18 · Retiros](18-retiros-y-ciclo-de-vida.md) · [🏠 Índice](../README.md)

</div>

---

## Contenido

1. [SLA de referencia](#1-sla-de-referencia)
2. [Límites y cifras clave](#2-límites-y-cifras-clave)
3. [Comandos esenciales de Azure CLI](#3-comandos-esenciales-de-azure-cli)
4. [Convenciones de nombres y etiquetas](#4-convenciones-de-nombres-y-etiquetas)
5. [Glosario](#5-glosario)
6. [Para seguir aprendiendo](#6-para-seguir-aprendiendo)

---

## 1. SLA de referencia

> [!CAUTION]
> Valores orientativos de las configuraciones más comunes. El SLA vigente depende del tier, de las zonas y de la
> configuración exacta: consulta siempre *Service Level Agreements for Online Services* antes de comprometer SLO.

| Servicio | Configuración | SLA |
|---|---|---|
| Virtual Machines | Dos o más VM en zonas distintas | 99,99 % |
| Virtual Machines | Availability set | 99,95 % |
| Virtual Machines | VM única con Premium SSD / Premium SSD v2 / Ultra | 99,9 % |
| AKS | API server, tier Standard/Premium con zonas | 99,95 % |
| AKS | API server, tier Standard/Premium sin zonas | 99,9 % |
| App Service / Functions / Container Apps | Planes de pago | 99,95 % |
| Cosmos DB | Una región sin zonas | 99,99 % |
| Cosmos DB | Una región con zonas | 99,995 % |
| Cosmos DB | Multirregión | 99,999 % |
| Azure SQL Database | General Purpose / Business Critical | 99,99 % |
| Azure SQL Database | Business Critical/Premium con redundancia de zona | 99,995 % |
| Storage | LRS/ZRS (lectura y escritura, Hot) | 99,9 % |
| Storage | RA-GRS / RA-GZRS (lectura) | 99,99 % |
| Front Door | Standard/Premium | 99,99 % |
| Load Balancer | Standard | 99,99 % |
| VPN Gateway / ExpressRoute | SKU de producción | 99,95 % |
| Service Bus / Event Hubs / Event Grid | Según tier | Consulta el documento oficial (los tiers dedicados ofrecen los valores más altos) |

| SLA | Inactividad máxima por mes (≈30 días) | Por año |
|---|---|---|
| 99 % | 7 h 12 min | 3,65 días |
| 99,9 % | 43 min | 8,8 h |
| 99,95 % | 22 min | 4,4 h |
| 99,99 % | 4,3 min | 53 min |
| 99,995 % | 2,2 min | 26 min |
| 99,999 % | 26 s | 5,3 min |

---

## 2. Límites y cifras clave

| Servicio | Cifra | Valor |
|---|---|---|
| AKS | Nodos por clúster / *node pools* / nodos por pool | 5 000 / 100 / 1 000 |
| AKS Fleet Manager | Clústeres miembro por *fleet* | 1 000 |
| Container Apps | Réplicas por revisión / recursos por réplica (Consumption) | 1 000 / 4 vCPU · 8 GiB |
| Functions Flex Consumption | Instancias máximas / memoria por instancia | 1 000 / 512 MB, 2 GB o 4 GB |
| Functions (HTTP) | Tiempo máximo de respuesta | 230 s |
| Cosmos DB | Partición lógica / partición física | 20 GB / 10 000 RU/s y 50 GB |
| Cosmos DB | Tamaño de ítem / niveles de clave jerárquica | 2 MB / 3 |
| Storage | Capacidad por cuenta (por defecto) / block blob máximo | 5 PiB / ~190,7 TiB |
| Service Bus | Mensaje Standard / Premium | 256 KB / 100 MB |
| Service Bus | Suscripciones por topic / ventana de duplicados | 2 000 / 7 días |
| Event Hubs | Evento / retención Premium-Dedicated | 1 MB / 90 días |
| Event Hubs | 1 TU (Standard) | 1 MB/s o 1 000 eventos/s de entrada |
| Event Grid | Evento / reintentos por defecto | 1 MB / 24 h (30 intentos) |
| Storage Queues | Mensaje | 64 KiB |
| NAT Gateway StandardV2 | Rendimiento | 100 Gbps · 10 M paquetes/s |
| Load Balancer Standard | Instancias de backend | 5 000 |
| Management groups | Profundidad | 6 niveles |
| SQL Hyperscale | Tamaño máximo / réplicas con nombre | 128 TB / 30 |

---

## 3. Comandos esenciales de Azure CLI

```bash
# Sesión y contexto
az login                                   # (o --use-device-code / --identity en VM con identidad administrada)
az account set --subscription "<id-o-nombre>"
az group create -n rg-demo-weu -l westeurope --tags env=dev owner=equipo-plataforma

# Infraestructura como código
az deployment group what-if -g rg-demo-weu -f main.bicep -p main.bicepparam
az stack group create -n stack-demo -g rg-demo-weu -f main.bicep -p main.bicepparam \
   --action-on-unmanage detachAll --deny-settings-mode none

# Contenedores
az aks create -g rg-demo-weu -n aks-demo --sku automatic
az aks get-credentials -g rg-demo-weu -n aks-demo
az containerapp up -n api-demo -g rg-demo-weu --source .          # build + deploy desde código

# Serverless (plan Flex Consumption)
az functionapp create -g rg-demo-weu -n func-demo-weu --flexconsumption-location westeurope \
   --runtime dotnet-isolated --runtime-version 10.0 --storage-account stdemoweu01

# Datos y mensajería
az cosmosdb create -g rg-demo-weu -n cosmos-demo \
   --locations regionName=westeurope failoverPriority=0 isZoneRedundant=true \
   --default-consistency-level Session
az servicebus namespace create -g rg-demo-weu -n sbns-demo --sku Premium --capacity 1
az eventhubs namespace create -g rg-demo-weu -n evhns-demo --sku Standard --enable-auto-inflate true \
   --maximum-throughput-units 10

# Identidad y acceso (RBAC sobre el plano de datos)
az role assignment create --assignee <principalId> --role "Azure Service Bus Data Receiver" \
   --scope $(az servicebus namespace show -g rg-demo-weu -n sbns-demo --query id -o tsv)

# Observabilidad e inventario
az monitor log-analytics query -w <workspaceId> --analytics-query "requests | take 10"
az graph query -q "resources | summarize count() by type | top 10 by count_"
```

---

## 4. Convenciones de nombres y etiquetas

Patrón recomendado por el Cloud Adoption Framework: **`<tipo>-<carga>-<entorno>-<región>-<instancia>`**,
por ejemplo `aks-pagos-prod-weu-001`.

| Recurso | Abreviatura | Ejemplo |
|---|---|---|
| Resource group | `rg` | `rg-pagos-prod-weu` |
| Virtual network / subnet | `vnet` / `snet` | `vnet-hub-prod-weu` |
| Network security group | `nsg` | `nsg-snet-app-prod` |
| Public IP | `pip` | `pip-agw-prod-weu` |
| Application Gateway | `agw` | `agw-portal-prod-weu` |
| Front Door (perfil) | `afd` | `afd-comercio-prod` |
| Firewall | `afw` | `afw-hub-prod-weu` |
| AKS | `aks` | `aks-pagos-prod-weu-001` |
| Container Apps / entorno | `ca` / `cae` | `ca-api-pedidos-prod` |
| Function app | `func` | `func-facturas-prod-weu` |
| App Service plan / web app | `asp` / `app` | `app-portal-prod-weu` |
| Container registry | `cr` | `crcomercioprod` (sin guiones) |
| Key Vault | `kv` | `kv-pagos-prod-weu` |
| Storage account | `st` | `stpagosprodweu01` (minúsculas, sin guiones, ≤ 24) |
| Cosmos DB | `cosmos` | `cosmos-pedidos-prod` |
| SQL server / database | `sql` / `sqldb` | `sqldb-ventas-prod` |
| Service Bus namespace / queue / topic | `sbns` / `sbq` / `sbt` | `sbns-comercio-prod` |
| Event Hubs namespace / hub | `evhns` / `evh` | `evhns-telemetria-prod` |
| API Management | `apim` | `apim-comercio-prod` |
| Log Analytics / Application Insights | `log` / `appi` | `appi-portal-prod` |
| Identidad administrada (usuario) | `id` | `id-api-pedidos-prod` |
| Private endpoint | `pep` | `pep-cosmos-pedidos-prod` |

**Etiquetas mínimas** (impuestas con Azure Policy): `env`, `owner`, `costCenter`, `app`, `criticality`,
`dataClassification`.

---

## 5. Glosario

| Término | Definición |
|---|---|
| **A2A** | *Agent-to-Agent*: protocolo abierto para que agentes de IA se comuniquen entre sí |
| **ACID** | Atomicidad, consistencia, aislamiento y durabilidad de las transacciones |
| **AMQP** | Protocolo de mensajería binario estándar (1.0) usado por Service Bus y Event Hubs |
| **Anycast** | Una misma IP anunciada desde muchos puntos; el usuario llega al más cercano (Front Door) |
| **ARM** | Azure Resource Manager, el plano de control de Azure |
| **Availability zone** | Datacenter(s) con infraestructura independiente dentro de una región |
| **BASE** | *Basically Available, Soft state, Eventually consistent*: alternativa a ACID en sistemas distribuidos |
| **Blast radius** | Alcance del daño de una falla o un cambio erróneo |
| **CAP / PACELC** | Teoremas sobre los compromisos entre consistencia, disponibilidad y latencia ante particiones |
| **Change feed** | Registro ordenado de cambios de Cosmos DB o Blob Storage |
| **Circuit breaker** | Patrón que corta llamadas a una dependencia degradada para que se recupere |
| **CloudEvents** | Especificación CNCF para describir eventos de forma estándar |
| **Consumer group** | Vista independiente de un *event hub* para una aplicación consumidora |
| **CQRS** | Separación de modelos de escritura (comandos) y lectura (consultas) |
| **Dapr** | *Distributed Application Runtime*: sidecar con *building blocks* para microservicios |
| **DLQ** | *Dead-letter queue*: cola de mensajes que no pudieron procesarse |
| **ETag** | Versión de un recurso usada para concurrencia optimista |
| **Event sourcing** | Persistir el estado como secuencia de eventos inmutables |
| **Failover** | Conmutación a una réplica o región secundaria ante una falla |
| **Geode** | Patrón de despliegue de nodos geográficos equivalentes que sirven a cualquier usuario |
| **Hot partition** | Partición que recibe una carga desproporcionada y se convierte en cuello de botella |
| **IaC** | Infraestructura como código (Bicep, Terraform) |
| **Idempotencia** | Propiedad de una operación que produce el mismo efecto si se repite |
| **KEDA** | *Kubernetes Event-driven Autoscaling*: escalado por eventos, incluso a cero |
| **KQL** | *Kusto Query Language*, lenguaje de Azure Monitor, Data Explorer, Sentinel y Resource Graph |
| **Landing zone** | Entorno base gobernado donde se despliegan las cargas de trabajo |
| **Lease** | Bloqueo temporal renovable para coordinar instancias (elección de líder) |
| **LRS / ZRS / GRS / GZRS** | Opciones de redundancia de Azure Storage (local, zona, geo, geo+zona) |
| **Managed identity** | Identidad de Entra ID administrada por Azure para un recurso, sin secretos |
| **MCP** | *Model Context Protocol*: protocolo abierto para exponer herramientas y datos a modelos y agentes |
| **mTLS** | TLS mutuo: cliente y servidor se autentican con certificados |
| **NVA** | *Network virtual appliance*: firewall o *router* de terceros como VM |
| **OIDC** | OpenID Connect; base de la federación de identidad de cargas |
| **OpenTelemetry** | Estándar abierto de trazas, métricas y logs |
| **Outbox** | Patrón que guarda el evento en la misma transacción que el dato y lo publica después |
| **Partition key** | Propiedad que decide en qué partición se guarda un dato (Cosmos DB, Event Hubs) |
| **Peek-lock** | Modo de recepción que bloquea el mensaje hasta confirmarlo o abandonarlo |
| **PITR** | *Point-in-time restore*: restaurar a un instante concreto |
| **Private endpoint** | Interfaz de red con IP privada para un servicio PaaS |
| **PTU** | *Provisioned throughput unit*: capacidad reservada para modelos de Foundry |
| **Quorum** | Mayoría de réplicas necesaria para confirmar una operación |
| **RAG** | *Retrieval-augmented generation*: generación aumentada con recuperación de conocimiento |
| **Raft** | Algoritmo de consenso (usado por etcd en Kubernetes) |
| **RPO / RTO** | Pérdida de datos máxima tolerable / tiempo máximo de recuperación |
| **RU** | *Request unit*: moneda de rendimiento de Cosmos DB |
| **Saga** | Secuencia de transacciones locales con compensaciones en lugar de 2PC |
| **SAS** | *Shared access signature*: token firmado de acceso delegado a Storage |
| **Sharding** | Repartir datos horizontalmente entre particiones |
| **Sidecar** | Contenedor auxiliar junto a la app que aporta capacidades transversales |
| **SLA / SLO / SLI** | Acuerdo contractual / objetivo interno / indicador medido |
| **SNAT** | Traducción de dirección de origen para tráfico saliente |
| **Stamp** | Unidad de despliegue repetible (celda) que aloja una fracción de usuarios |
| **TU / PU / CU** | Unidades de capacidad de Event Hubs (Standard / Premium / Dedicated) |
| **TTL** | *Time to live*: caducidad automática de datos o mensajes |
| **vCore** | Modelo de compra de bases de datos por núcleos virtuales |
| **W3C Trace Context** | Estándar de propagación de trazas (`traceparent`, `tracestate`) |
| **WAF** | *Web Application Firewall* **o** *Well-Architected Framework* (según contexto) |
| **Zero Trust** | Modelo de seguridad: verificar explícitamente, mínimo privilegio, asumir la brecha |

---

## 6. Para seguir aprendiendo

| Recurso | Para qué |
|---|---|
| [Microsoft Learn — Azure](https://learn.microsoft.com/azure/) | Documentación oficial y rutas de aprendizaje |
| [Azure Architecture Center](https://learn.microsoft.com/azure/architecture/) | Arquitecturas de referencia, patrones y guías de decisión |
| [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/) | Guías por pilar y por servicio |
| [Azure Updates](https://azure.microsoft.com/updates/) | Novedades, *previews* y retiros |
| [Azure SDK](https://azure.github.io/azure-sdk/) | Guías de diseño y versiones de los SDK |
| [AKS release notes](https://github.com/Azure/AKS/releases) | Cambios semanales de AKS |
| [Azure Charts](https://azurecharts.com/) (comunidad) | Visualizaciones de actualizaciones y disponibilidad |

---

<div align="center">

[⬅ 18 · Retiros](18-retiros-y-ciclo-de-vida.md) · [🏠 Índice](../README.md)

</div>
