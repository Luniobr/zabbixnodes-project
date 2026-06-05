"""Aguarda o banco de dados ficar pronto para aceitar queries.

Faz uma conexão REAL via asyncpg (já é dependência do projeto), validando
não apenas a porta TCP, mas também credenciais e existência do database.

Diferente de checagens só de porta (nc / socket), distingue:
  - banco ainda subindo / porta fechada  -> continua tentando
  - usuário/senha errados                 -> falha rápido com mensagem clara
  - database inexistente                  -> falha rápido com mensagem clara

Configurável por variáveis de ambiente:
  DB_WAIT_MAX_ATTEMPTS (padrão 60)
  DB_WAIT_INTERVAL     (padrão 2 segundos)
"""

import asyncio
import os
import sys

import asyncpg

MAX_ATTEMPTS = int(os.getenv("DB_WAIT_MAX_ATTEMPTS", "60"))
RETRY_INTERVAL = float(os.getenv("DB_WAIT_INTERVAL", "2"))
CONNECT_TIMEOUT = float(os.getenv("DB_WAIT_CONNECT_TIMEOUT", "5"))


def _to_asyncpg_dsn(url: str) -> str:
    """Remove o sufixo de driver do SQLAlchemy: asyncpg não entende '+asyncpg'."""
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def _try_connect(dsn: str) -> None:
    conn = await asyncpg.connect(dsn, timeout=CONNECT_TIMEOUT)
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()


async def main() -> int:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL não definida", flush=True)
        return 1

    dsn = _to_asyncpg_dsn(url)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            await _try_connect(dsn)
            print("   ✓ Banco de dados pronto (conexão + query OK)", flush=True)
            return 0

        except asyncpg.InvalidPasswordError:
            # Credenciais erradas não se resolvem esperando.
            print("❌ Falha de autenticação no banco de dados.", flush=True)
            print("   Verifique usuário/senha no DATABASE_URL.", flush=True)
            print("   Causa comum: volume Postgres antigo, criado com outras credenciais.", flush=True)
            return 2

        except asyncpg.InvalidCatalogNameError:
            # Database inexistente também não se resolve esperando.
            print("❌ O database informado no DATABASE_URL não existe.", flush=True)
            print("   Verifique o nome do banco ou se o volume foi inicializado corretamente.", flush=True)
            return 3

        except (OSError, asyncpg.PostgresError, asyncio.TimeoutError) as exc:
            # Porta fechada, DNS ainda não resolve, servidor em startup/recovery, etc.
            if attempt % 10 == 0:
                print(
                    f"   ⏳ Tentativa {attempt}/{MAX_ATTEMPTS}: aguardando ({type(exc).__name__})",
                    flush=True,
                )
            await asyncio.sleep(RETRY_INTERVAL)

    print(f"❌ Banco de dados não respondeu após {MAX_ATTEMPTS} tentativas.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
