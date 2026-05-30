# ZabbixNodes Project

## From Legacy Distributed Monitoring to Modern Multi-Instance Orchestration

ZabbixNodes Project is an open-source initiative focused on exploring modern approaches to orchestrating, governing, and providing centralized visibility across multiple independent Zabbix environments.

Inspired by the historical Zabbix Nodes architecture, the project investigates how organizations, managed service providers (MSPs), system integrators, and enterprise operations teams can efficiently manage distributed monitoring environments at scale.

> This project is currently under active research and development.

---

# Why ZabbixNodes?

As monitoring environments continue to grow, it becomes increasingly common to manage:

* Multiple Zabbix instances
* Multiple datacenters
* Hybrid and multi-cloud environments
* Multiple business units
* Multiple customers
* Distributed operations teams

Zabbix already provides powerful capabilities through Proxies, APIs, Discovery, Templates, Integrations, and Automation.

However, many organizations still face challenges related to:

* Centralized visibility
* Unified governance
* Inventory consolidation
* Cross-instance management
* Operational standardization
* Administrative scalability

ZabbixNodes aims to explore these challenges and propose a modern approach to multi-instance orchestration.

---

# Vision

One operational view.

Multiple Zabbix environments.

Centralized governance.

Greater visibility.

Scalable operations.

---

# Current Status

The project is currently in its research, architecture, and validation phase.

## Progress

* [x] Requirements Research
* [x] Historical Analysis of Legacy Zabbix Nodes
* [x] Project Vision Definition
* [x] Initial Architecture Design
* [x] Proof of Concept (PoC)
* [x] Alpha Release
* [ ] Community Preview
* [ ] Beta Release
* [ ] First Public Release

At this stage, the source code remains private while concepts, architecture, and implementation strategies are being refined and validated.

---

# Architecture Concept

```text
                   +----------------+
                   |  ZabbixNodes   |
                   | Control Plane  |
                   +--------+-------+
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v

 +-------------+    +-------------+    +-------------+
 | Zabbix A    |    | Zabbix B    |    | Zabbix C    |
 | Datacenter  |    | Cloud       |    | MSP Client  |
 +-------------+    +-------------+    +-------------+

        ^                   ^                   ^
        |                   |                   |
       API                 API                 API
```

This diagram represents the conceptual vision of the project and does not necessarily reflect the final implementation.

---

# Roadmap

## Phase 1 — Foundation

* Multi-instance registration
* Centralized inventory
* Data consolidation
* Unified dashboard

## Phase 2 — Federation

* Cross-instance visibility
* Controlled information sharing
* Object synchronization
* Distributed governance

## Phase 3 — Advanced Operations

* Centralized auditing
* Compliance
* Multi-tenant management
* Operational intelligence

---

# Community

ZabbixNodes Project is an open community initiative currently under development.

Welcome feedback, ideas, discussions, and collaboration from the monitoring and observability community.

## Stay Connected

- Website: <https://luniobr.com>
- LinkedIn: <https://www.linkedin.com/company/luniobr>
- Instagram: <https://www.instagram.com/lunio.br>
- Contact: <hernandes.martins@luniobr.com>

Community resources, discussion groups, issue tracking, and contribution guidelines will be published in future releases.

Thank you for your interest in the new ZabbixNodesManager Project.


---

# Origin

The idea behind ZabbixNodes emerged from studies of the original Zabbix Nodes architecture and from real-world challenges observed in enterprise monitoring environments, managed service providers (MSPs), and large-scale distributed operations.

The goal is not to recreate the legacy Zabbix Nodes solution, but rather to explore a modern architecture for orchestrating and managing multiple Zabbix environments.

---

# Official Presentation

The project concept will be publicly presented during:

**"Dos Zabbix Nodes à Orquestração de Múltiplas Instâncias Zabbix"(pt-br)**
**"From Legacy Zabbix Nodes to Modern Multi-Instance Orchestration"(en-gb)**

Zabbix Conference LATAM 2026 - Hernandes Martins

# License

Source code is not yet publicly available.

Licensing information will be announced when the first public release becomes available.
