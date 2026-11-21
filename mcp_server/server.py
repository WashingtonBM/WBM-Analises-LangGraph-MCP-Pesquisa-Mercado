import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

ARQUIVO_RESPOSTAS = (
    Path(__file__).resolve().parents[1] / "data" / "respostas_pesquisa.json"
)
mcp = FastMCP("wbm-pesquisa-mercado")


def _carregar_respostas() -> list[dict[str, Any]]:
    if not ARQUIVO_RESPOSTAS.exists():
        return []

    dados = json.loads(ARQUIVO_RESPOSTAS.read_text(encoding="utf-8"))
    if not isinstance(dados, list) or not all(
        isinstance(item, dict) for item in dados
    ):
        raise ValueError(f"O arquivo {ARQUIVO_RESPOSTAS} deve conter uma lista JSON de objetos.")
    return dados


def _salvar_respostas(respostas: list[dict[str, Any]]) -> None:
    ARQUIVO_RESPOSTAS.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_RESPOSTAS.write_text(
        json.dumps(respostas, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalizar_resposta(
    segmento: str,
    controle_atual: str,
    dor_relatada: str,
    maior_gargalo: str,
    formato_preferido: str,
) -> dict[str, str]:
    resposta = {
        "segmento": segmento.strip(),
        "controle_atual": controle_atual.strip(),
        "dor_relatada": dor_relatada.strip(),
        "maior_gargalo": maior_gargalo.strip(),
        "formato_preferido": formato_preferido.strip(),
    }
    if not any(resposta.values()):
        raise ValueError("Informe pelo menos um campo da resposta.")
    return resposta


def _registrar_resposta(resposta: dict[str, str]) -> str:
    respostas = _carregar_respostas()
    respostas.append(resposta)
    _salvar_respostas(respostas)
    return f"Resposta registrada. Total armazenado: {len(respostas)}."


@mcp.tool()
def listar_respostas() -> list[dict[str, Any]]:
    """Lista as respostas salvas pelo servidor MCP."""
    return _carregar_respostas()


@mcp.tool()
def adicionar_resposta(
    segmento: str = "",
    controle_atual: str = "",
    dor_relatada: str = "",
    maior_gargalo: str = "",
    formato_preferido: str = "",
) -> str:
    """Adiciona uma resposta à coleção persistida em arquivo JSON (compatibilidade)."""
    resposta = _normalizar_resposta(
        segmento,
        controle_atual,
        dor_relatada,
        maior_gargalo,
        formato_preferido,
    )
    return _registrar_resposta(resposta)


@mcp.tool()
def salvar_resposta_pesquisa(
    segmento: str,
    controle_atual: str,
    dor_relatada: str,
    maior_gargalo: str,
    formato_preferido: str,
) -> str:
    """Salva uma resposta estruturada da pesquisa de mercado em JSON."""
    resposta = _normalizar_resposta(
        segmento,
        controle_atual,
        dor_relatada,
        maior_gargalo,
        formato_preferido,
    )
    return _registrar_resposta(resposta)


@mcp.tool()
def salvar_lote_respostas(respostas: list[dict[str, Any]]) -> str:
    """Salva um lote de respostas da pesquisa no arquivo persistente."""
    if not all(isinstance(resposta, dict) for resposta in respostas):
        raise ValueError("O lote deve conter somente objetos de resposta.")

    registros = _carregar_respostas()
    registros.extend(respostas)
    _salvar_respostas(registros)
    return f"Lote salvo com sucesso. Total de registros: {len(registros)}."


@mcp.tool()
def listar_respostas_pesquisa() -> str:
    """Retorna todas as respostas coletadas em formato JSON."""
    return json.dumps(_carregar_respostas(), ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
