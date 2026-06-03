import asyncio
import time
from typing import Any

from core.config import settings
from services.zabbix import get_zabbix_client


async def calculate_health_score(url: str, api_token_encrypted: bytes) -> dict[str, Any]:
    """
    Calcula o Health Score (0-100) de uma instância Zabbix.

    Dimensões:
      - Conectividade    25pts — latência da API
      - Problemas ativos 30pts — triggers por severidade
      - Proxies          20pts — lastaccess dos proxies
      - Hosts ativos     15pts — % de hosts monitorados
      - Versão Zabbix    10pts — suporte 6.x/7.x
    """
    start = time.monotonic()
    try:
        zapi = await get_zabbix_client(url, api_token_encrypted)
    except Exception as e:
        return {
            "score": None,
            "label": None,
            "color": None,
            "connection_status": "offline",
            "error": str(e),
            "dimensions": {},
        }

    try:
        latency_ms = round((time.monotonic() - start) * 1000, 1)

        version_task = zapi.apiinfo.version()
        problems_task = zapi.trigger.get(
            output=["triggerid", "priority"],
            value=1,
            monitored=True,
            skipDependent=True,
            countOutput=False,
        )
        proxies_task = zapi.proxy.get(
            output=["proxyid", "name", "lastaccess"],
        )
        hosts_task = zapi.host.get(
            output=["hostid", "status"],
            countOutput=False,
        )

        version, triggers, proxies, hosts = await asyncio.gather(
            asyncio.wait_for(version_task, timeout=settings.ZABBIX_TIMEOUT_SECONDS),
            asyncio.wait_for(problems_task, timeout=settings.ZABBIX_TIMEOUT_SECONDS),
            asyncio.wait_for(proxies_task, timeout=settings.ZABBIX_TIMEOUT_SECONDS),
            asyncio.wait_for(hosts_task, timeout=settings.ZABBIX_TIMEOUT_SECONDS),
        )

        # --- Dimensão 1: Conectividade (25pts) ---
        if latency_ms < 500:
            conn_score = 25
            conn_status = "Excelente"
        elif latency_ms < 1000:
            conn_score = 18
            conn_status = "Boa"
        elif latency_ms < 2000:
            conn_score = 10
            conn_status = "Lenta"
        else:
            conn_score = 5
            conn_status = "Muito lenta"

        # --- Dimensão 2: Problemas ativos (30pts) ---
        severities = [int(t.get("priority", 0)) for t in triggers]
        has_disaster = any(s == 5 for s in severities)
        has_high     = any(s == 4 for s in severities)
        has_average  = any(s == 3 for s in severities)
        has_warning  = any(s == 2 for s in severities)
        total_probs  = len(severities)

        if total_probs == 0:
            prob_score = 30
            prob_status = "Sem problemas"
        elif has_disaster:
            prob_score = 0
            prob_status = f"Disaster ativo ({total_probs} problema(s))"
        elif has_high:
            prob_score = 8
            prob_status = f"High ativo ({total_probs} problema(s))"
        elif has_average:
            prob_score = 15
            prob_status = f"Average ativo ({total_probs} problema(s))"
        elif has_warning:
            prob_score = 22
            prob_status = f"Warning ativo ({total_probs} problema(s))"
        else:
            prob_score = 28
            prob_status = f"Info ativo ({total_probs} problema(s))"

        # --- Dimensão 3: Proxies (20pts) ---
        if not proxies:
            # Sem proxies configurados = N/A = score cheio
            proxy_score = 20
            proxy_status = "Sem proxies (N/A)"
        else:
            now = int(time.time())
            stale_threshold = 300  # 5 minutos
            stale = sum(1 for p in proxies if (now - int(p.get("lastaccess", 0))) > stale_threshold)
            total_px = len(proxies)
            ratio_ok = (total_px - stale) / total_px
            proxy_score = round(ratio_ok * 20)
            if stale == 0:
                proxy_status = f"{total_px} proxy(s) — todos ativos"
            else:
                proxy_status = f"{stale}/{total_px} proxy(s) sem resposta"

        # --- Dimensão 4: Hosts monitorados (15pts) ---
        total_hosts = len(hosts)
        if total_hosts == 0:
            host_score = 15
            host_status = "Sem hosts"
        else:
            disabled = sum(1 for h in hosts if str(h.get("status", "0")) == "1")
            ratio_active = (total_hosts - disabled) / total_hosts
            if ratio_active >= 1.0:
                host_score = 15
            elif ratio_active >= 0.90:
                host_score = 12
            elif ratio_active >= 0.70:
                host_score = 7
            else:
                host_score = 2
            pct = round(ratio_active * 100)
            host_status = f"{total_hosts - disabled}/{total_hosts} hosts ativos ({pct}%)"

        # --- Dimensão 5: Versão Zabbix (10pts) ---
        major = int(str(version).split(".")[0]) if version else 0
        if major >= 7:
            ver_score = 10
            ver_status = f"Zabbix {version} (suportado)"
        elif major == 6:
            ver_score = 10
            ver_status = f"Zabbix {version} (suportado)"
        elif major == 5:
            ver_score = 6
            ver_status = f"Zabbix {version} (suporte limitado)"
        else:
            ver_score = 0
            ver_status = f"Zabbix {version} (não suportado)"

        total = conn_score + prob_score + proxy_score + host_score + ver_score

        if total >= 90:
            label = "Excelente"
            color = "health-excellent"
        elif total >= 70:
            label = "Saudável"
            color = "health-healthy"
        elif total >= 40:
            label = "Atenção"
            color = "health-warning"
        else:
            label = "Crítico"
            color = "health-critical"

        if latency_ms < 500:
            connection_status = "online"
        elif latency_ms < 2000:
            connection_status = "slow"
        else:
            connection_status = "slow"

        return {
            "score": total,
            "label": label,
            "color": color,
            "connection_status": connection_status,
            "latency_ms": latency_ms,
            "zabbix_version": version,
            "error": None,
            "dimensions": {
                "connectivity": {"score": conn_score, "max": 25, "status": conn_status},
                "problems":     {"score": prob_score, "max": 30, "status": prob_status},
                "proxies":      {"score": proxy_score, "max": 20, "status": proxy_status},
                "hosts":        {"score": host_score,  "max": 15, "status": host_status},
                "version":      {"score": ver_score,   "max": 10, "status": ver_status},
            },
        }

    except Exception as e:
        return {
            "score": None,
            "label": None,
            "color": None,
            "connection_status": "offline",
            "error": str(e),
            "dimensions": {},
        }
    finally:
        try:
            await zapi.logout()
        except Exception:
            pass
