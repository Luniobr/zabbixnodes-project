import asyncio
import logging
import re
import time
from typing import Any

from zabbix_utils import AsyncZabbixAPI

from core.config import settings
from core.security import decrypt_token

logger = logging.getLogger("zabbixnodes.zabbix")


async def get_zabbix_client(url: str, api_token_encrypted: bytes) -> AsyncZabbixAPI:
    import json as _json
    decrypted = decrypt_token(api_token_encrypted)
    zapi = AsyncZabbixAPI(url=url, skip_version_check=True)
    try:
        creds = _json.loads(decrypted)
        if creds.get("type") == "credentials":
            await asyncio.wait_for(
                zapi.login(user=creds["user"], password=creds["password"]),
                timeout=settings.ZABBIX_TIMEOUT_SECONDS,
            )
        else:
            await asyncio.wait_for(
                zapi.login(token=creds["token"]),
                timeout=settings.ZABBIX_TIMEOUT_SECONDS,
            )
    except (_json.JSONDecodeError, KeyError):
        # Legacy format: raw token string
        await asyncio.wait_for(
            zapi.login(token=decrypted),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
    return zapi


async def test_connection(url: str, api_token_encrypted: bytes) -> dict[str, Any]:
    start = time.monotonic()
    try:
        zapi = await get_zabbix_client(url, api_token_encrypted)
        version = await asyncio.wait_for(zapi.apiinfo.version(), timeout=settings.ZABBIX_TIMEOUT_SECONDS)
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        await zapi.logout()
        return {"success": True, "version": version, "latency_ms": latency_ms}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_instance_stats(url: str, api_token_encrypted: bytes) -> dict[str, Any]:
    start = time.monotonic()
    try:
        zapi = await get_zabbix_client(url, api_token_encrypted)

        version_task = zapi.apiinfo.version()
        hosts_task = zapi.host.get(countOutput=True)
        problems_task = zapi.problem.get(countOutput=True, severities=[2, 3, 4, 5])

        version, total_hosts, problems = await asyncio.gather(
            asyncio.wait_for(version_task, timeout=settings.ZABBIX_TIMEOUT_SECONDS),
            asyncio.wait_for(hosts_task, timeout=settings.ZABBIX_TIMEOUT_SECONDS),
            asyncio.wait_for(problems_task, timeout=settings.ZABBIX_TIMEOUT_SECONDS),
        )

        latency_ms = round((time.monotonic() - start) * 1000, 1)
        await zapi.logout()

        return {
            "success": True,
            "version": version,
            "total_hosts": int(total_hosts),
            "hosts_in_problem": int(problems),
            "latency_ms": latency_ms,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def list_hosts(url: str, api_token_encrypted: bytes, group_id: str | None = None) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        params: dict[str, Any] = {
            "output": ["hostid", "host", "name", "status", "description"],
            "selectGroups": ["groupid", "name"],
            "selectParentTemplates": ["templateid", "name"],
            "selectInterfaces": ["interfaceid", "type", "main", "useip", "ip", "dns", "port"],
            "selectMonitoringProxy": ["proxyid", "name"],
        }
        if group_id:
            params["groupids"] = [group_id]

        hosts = await asyncio.wait_for(
            zapi.host.get(**params),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return hosts
    finally:
        await zapi.logout()


async def create_host(url: str, api_token_encrypted: bytes, data: dict) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.host.create(**data),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def update_host(url: str, api_token_encrypted: bytes, host_id: str, data: dict) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.host.update(hostid=host_id, **data),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def delete_host(url: str, api_token_encrypted: bytes, host_id: str) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.host.delete(host_id),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def toggle_host(url: str, api_token_encrypted: bytes, host_id: str, enable: bool) -> dict:
    status = 0 if enable else 1
    return await update_host(url, api_token_encrypted, host_id, {"status": status})


async def list_host_groups(url: str, api_token_encrypted: bytes) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        groups = await asyncio.wait_for(
            zapi.hostgroup.get(output=["groupid", "name"]),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return groups
    finally:
        await zapi.logout()


async def list_templates(url: str, api_token_encrypted: bytes) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        templates = await asyncio.wait_for(
            zapi.template.get(output=["templateid", "name", "description"]),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return templates
    finally:
        await zapi.logout()


async def create_host_group(url: str, api_token_encrypted: bytes, name: str) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.hostgroup.create(name=name),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def update_host_group(url: str, api_token_encrypted: bytes, group_id: str, name: str) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.hostgroup.update(groupid=group_id, name=name),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def delete_host_group(url: str, api_token_encrypted: bytes, group_id: str) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.hostgroup.delete(group_id),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def get_template_by_name(url: str, api_token_encrypted: bytes, name: str) -> dict | None:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.template.get(filter={"name": name}, output=["templateid", "name"]),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result[0] if result else None
    finally:
        await zapi.logout()


async def count_template_items(url: str, api_token_encrypted: bytes, templateid: str) -> int:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.item.get(templateids=[templateid], countOutput=True),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return int(result)
    finally:
        await zapi.logout()


# Fields to strip before calling item.create.
# Includes read-only runtime fields AND legacy fields removed in newer Zabbix versions
# that older instances reject as "unexpected parameter".
_ITEM_EXCLUDE = frozenset({
    # Read-only / auto-generated
    "itemid", "templateid", "flags", "state", "error",
    "lastvalue", "lastclock", "prevvalue", "lastns",
    # Legacy fields removed in Zabbix 4.x / 5.x — newer instances still return them
    # in item.get output but older ones reject them in item.create (and vice-versa)
    "formula", "multiplier", "delta",
})


def _prepare_item_create(item: dict, target_hostid: str) -> dict:
    """Strip incompatible fields and set correct hostid for item.create."""
    data = {k: v for k, v in item.items() if k not in _ITEM_EXCLUDE}
    data["hostid"] = target_hostid
    # Value maps are instance-specific; clear to avoid cross-instance errors
    if data.get("valuemapid", "0") not in ("0", 0):
        data["valuemapid"] = "0"
    return data


async def get_template_items(url: str, api_token_encrypted: bytes, templateid: str) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        items = await asyncio.wait_for(
            zapi.item.get(
                templateids=[templateid],
                output="extend",
                selectPreprocessing="extend",
                selectTags="extend",
            ),
            timeout=30,
        )
        return items
    finally:
        await zapi.logout()


async def sync_template_items(
    ref_url: str,
    ref_token: bytes,
    ref_templateid: str,
    target_url: str,
    target_token: bytes,
    target_templateid: str,
) -> list[dict]:
    """Create items missing in target compared to reference. Returns per-item results."""
    ref_items = await get_template_items(ref_url, ref_token, ref_templateid)
    target_items = await get_template_items(target_url, target_token, target_templateid)

    ref_by_id = {item["itemid"]: item for item in ref_items}
    target_by_key: dict[str, str] = {item["key_"]: item["itemid"] for item in target_items}

    # Only process manually-created items (flags=0); skip LLD-discovered (flags=4)
    missing = [
        item for item in ref_items
        if item["key_"] not in target_by_key and str(item.get("flags", "0")) == "0"
    ]

    regular = [i for i in missing if str(i.get("type", "0")) != "18"]
    dependent = [i for i in missing if str(i.get("type", "0")) == "18"]

    async def _create_item(data: dict) -> str:
        """Create item with automatic field stripping and session recovery.

        When Zabbix rejects an 'unexpected parameter', the offending field is
        stripped and the call is retried — handles version mismatches without
        a hard-coded exclusion list.  Session-closed errors trigger a reconnect.
        """
        nonlocal zapi
        current = dict(data)

        for _ in range(20):  # guard against infinite loops
            try:
                res = await asyncio.wait_for(zapi.item.create(**current), timeout=30)
                return res["itemids"][0]
            except Exception as e:
                err = str(e)

                # Auto-strip unknown/unsupported fields
                m = re.search(r'unexpected parameter "([^"]+)"', err)
                if m:
                    bad_field = m.group(1)
                    logger.info("item.create: stripping unsupported field '%s' for key '%s'",
                                bad_field, current.get("key_", "?"))
                    current.pop(bad_field, None)
                    # Reconnect — some Zabbix versions close session after bad request
                    try:
                        await zapi.logout()
                    except Exception:
                        pass
                    zapi = await get_zabbix_client(target_url, target_token)
                    continue

                # Session closed — reconnect once and retry
                if "session" in err.lower() or "closed" in err.lower():
                    try:
                        await zapi.logout()
                    except Exception:
                        pass
                    zapi = await get_zabbix_client(target_url, target_token)
                    res = await asyncio.wait_for(zapi.item.create(**current), timeout=30)
                    return res["itemids"][0]

                raise

        raise RuntimeError("item.create falhou após remover múltiplos campos incompatíveis")

    results: list[dict] = []
    zapi = await get_zabbix_client(target_url, target_token)
    try:
        # Pass 1: non-dependent items
        for item in regular:
            try:
                data = _prepare_item_create(item, target_templateid)
                new_id = await _create_item(data)
                target_by_key[item["key_"]] = new_id
                results.append({"key_": item["key_"], "name": item["name"], "created": True})
            except Exception as e:
                results.append({"key_": item["key_"], "name": item["name"], "created": False, "error": str(e)})
                # Reconnect so next item starts with a fresh session
                try:
                    await zapi.logout()
                except Exception:
                    pass
                zapi = await get_zabbix_client(target_url, target_token)

        # Pass 2: dependent items (master must exist first)
        for item in dependent:
            try:
                data = _prepare_item_create(item, target_templateid)
                ref_master = ref_by_id.get(str(item.get("master_itemid", "")))
                if ref_master:
                    master_id = target_by_key.get(ref_master["key_"])
                    if not master_id:
                        raise ValueError(f"Item mestre '{ref_master['key_']}' não encontrado no alvo")
                    data["master_itemid"] = master_id
                new_id = await _create_item(data)
                target_by_key[item["key_"]] = new_id
                results.append({"key_": item["key_"], "name": item["name"], "created": True})
            except Exception as e:
                results.append({"key_": item["key_"], "name": item["name"], "created": False, "error": str(e)})
                try:
                    await zapi.logout()
                except Exception:
                    pass
                zapi = await get_zabbix_client(target_url, target_token)
    finally:
        try:
            await zapi.logout()
        except Exception:
            pass

    return results


async def list_template_groups(url: str, api_token_encrypted: bytes) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        # Zabbix 6.0+ has templategroup; fallback to hostgroup for older versions
        try:
            groups = await asyncio.wait_for(
                zapi.templategroup.get(output=["groupid", "name"]),
                timeout=settings.ZABBIX_TIMEOUT_SECONDS,
            )
        except Exception:
            groups = await asyncio.wait_for(
                zapi.hostgroup.get(output=["groupid", "name"]),
                timeout=settings.ZABBIX_TIMEOUT_SECONDS,
            )
        return sorted(groups, key=lambda g: g["name"].lower())
    finally:
        await zapi.logout()


async def create_template(url: str, api_token_encrypted: bytes, data: dict) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.template.create(**data),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def update_template(url: str, api_token_encrypted: bytes, templateid: str, data: dict) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.template.update(templateid=templateid, **data),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def get_template_detail(url: str, api_token_encrypted: bytes, templateid: str) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        templates = await asyncio.wait_for(
            zapi.template.get(
                templateids=[templateid],
                output=["templateid", "name", "description"],
                selectHosts=["hostid", "host", "name", "status"],
                selectGroups=["groupid", "name"],
                selectItems=["itemid"],
            ),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        if not templates:
            raise ValueError("Template não encontrado")
        t = templates[0]
        t["items_count"] = len(t.pop("items", []))
        return t
    finally:
        await zapi.logout()


async def list_templates_with_counts(url: str, api_token_encrypted: bytes) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        templates = await asyncio.wait_for(
            zapi.template.get(
                output=["templateid", "name", "description"],
                selectHosts=["hostid"],
                selectItems=["itemid"],
            ),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        for t in templates:
            t["hosts_count"] = len(t.pop("hosts", []))
            t["items_count"] = len(t.pop("items", []))
        return sorted(templates, key=lambda x: x["name"].lower())
    finally:
        await zapi.logout()


async def link_template_to_hosts(
    url: str, api_token_encrypted: bytes, templateid: str, host_ids: list[str]
) -> None:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        for host_id in host_ids:
            host = await asyncio.wait_for(
                zapi.host.get(hostids=[host_id], output=["hostid"], selectParentTemplates=["templateid"]),
                timeout=settings.ZABBIX_TIMEOUT_SECONDS,
            )
            if not host:
                continue
            existing = [t["templateid"] for t in host[0].get("parentTemplates", [])]
            if templateid not in existing:
                existing.append(templateid)
            await asyncio.wait_for(
                zapi.host.update(hostid=host_id, templates=[{"templateid": tid} for tid in existing]),
                timeout=settings.ZABBIX_TIMEOUT_SECONDS,
            )
    finally:
        await zapi.logout()


async def unlink_template_from_host(
    url: str, api_token_encrypted: bytes, templateid: str, host_id: str
) -> None:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        await asyncio.wait_for(
            zapi.host.update(
                hostid=host_id,
                templates_clear=[{"templateid": templateid}],
            ),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
    finally:
        await zapi.logout()


async def delete_template(url: str, api_token_encrypted: bytes, templateid: str) -> None:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        await asyncio.wait_for(
            zapi.template.delete(templateid),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
    finally:
        await zapi.logout()


async def list_proxies(url: str, api_token_encrypted: bytes) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        proxies = await asyncio.wait_for(
            zapi.proxy.get(output=["proxyid", "name", "operating_mode", "description", "lastaccess"]),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return proxies
    finally:
        await zapi.logout()


async def create_proxy(url: str, api_token_encrypted: bytes, data: dict) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.proxy.create(**data),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def delete_proxy(url: str, api_token_encrypted: bytes, proxy_id: str) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.proxy.delete(proxy_id),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def list_triggers(
    url: str,
    api_token_encrypted: bytes,
    only_problems: bool = True,
    group_id: str | None = None,
    host_id: str | None = None,
    min_severity: int = 0,
) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        params: dict[str, Any] = {
            "output": ["triggerid", "description", "priority", "lastchange", "comments", "url"],
            "selectHosts": ["hostid", "host", "name"],
            "selectLastEvent": ["eventid", "acknowledged", "clock", "severity"],
            "expandDescription": True,
            "monitored": True,
            "skipDependent": True,
            "sortfield": "lastchange",
            "sortorder": "DESC",
        }
        if only_problems:
            params["value"] = 1  # 1 = in problem state
        if min_severity > 0:
            params["min_severity"] = min_severity
        if group_id:
            params["groupids"] = [group_id]
        if host_id:
            params["hostids"] = [host_id]

        triggers = await asyncio.wait_for(
            zapi.trigger.get(**params),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return triggers
    finally:
        await zapi.logout()


async def acknowledge_event(
    url: str,
    api_token_encrypted: bytes,
    event_id: str,
    message: str = "",
) -> dict:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        result = await asyncio.wait_for(
            zapi.event.acknowledge(
                eventids=[event_id],
                action=6,  # 2=ack + 4=add message
                message=message or "Reconhecido via ZabbixNodes",
            ),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return result
    finally:
        await zapi.logout()


async def list_host_items(
    url: str,
    api_token_encrypted: bytes,
    host_id: str,
    search: str | None = None,
) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        params: dict[str, Any] = {
            "hostids": [host_id],
            "output": ["itemid", "name", "key_", "type", "value_type", "units",
                       "delay", "lastvalue", "lastclock", "status", "state", "error"],
            "sortfield": "name",
            "sortorder": "ASC",
        }
        if search:
            params["search"] = {"name": search}
            params["searchWildcardsEnabled"] = True

        items = await asyncio.wait_for(
            zapi.item.get(**params),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return items
    finally:
        await zapi.logout()


async def get_item_history(
    url: str,
    api_token_encrypted: bytes,
    item_id: str,
    value_type: int,
    limit: int = 100,
) -> list[dict]:
    zapi = await get_zabbix_client(url, api_token_encrypted)
    try:
        # value_type: 0=float, 1=str, 2=log, 3=int, 4=text
        history = await asyncio.wait_for(
            zapi.history.get(
                itemids=[item_id],
                history=value_type,
                sortfield="clock",
                sortorder="DESC",
                limit=limit,
            ),
            timeout=settings.ZABBIX_TIMEOUT_SECONDS,
        )
        return history
    finally:
        await zapi.logout()
