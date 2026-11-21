import asyncio
import json
from pathlib import Path
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from graph.workflow import build_graph

RAIZ_PROJETO = Path(__file__).resolve().parent
ARQUIVO_EXEMPLO = RAIZ_PROJETO / "data" / "respostas_exemplo.json"


def exibir_resultado(titulo: str, resultado: dict[str, Any]) -> None:
    print("=" * 64)
    print(titulo)
    print("=" * 64)
    print(f"Status:           {resultado['status_execucao']}")
    print(f"Total respostas:  {resultado['total_respostas']}")
    print(f"Segmento foco:    {resultado['segmento_foco']}")
    print(f"Dor principal:    {resultado['dor_principal']}")
    print(f"Promessa única:   {resultado['promessa_unica']}")
    print(f"Script WhatsApp:  {resultado['mensagem_whatsapp']}")
    print()


def decodificar_respostas(dados: str) -> list[dict[str, Any]]:
    respostas = json.loads(dados)
    if not isinstance(respostas, list) or not all(
        isinstance(item, dict) for item in respostas
    ):
        raise ValueError("O servidor MCP deve retornar uma lista JSON de objetos.")
    return respostas


def texto_resultado_mcp(resultado: Any) -> str:
    if resultado.isError:
        raise RuntimeError(f"A chamada da ferramenta MCP falhou: {resultado.content}")
    if not resultado.content or not hasattr(resultado.content[0], "text"):
        raise RuntimeError("A ferramenta MCP não retornou conteúdo de texto.")
    return resultado.content[0].text


async def executar_pipeline_com_mcp() -> None:
    parametros_servidor = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.server"],
        cwd=str(RAIZ_PROJETO),
    )
    app = build_graph()

    async with stdio_client(parametros_servidor) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()

            resultado_mcp = await sessao.call_tool("listar_respostas_pesquisa", {})
            respostas = decodificar_respostas(texto_resultado_mcp(resultado_mcp))

            if not respostas:
                respostas_exemplo = json.loads(
                    ARQUIVO_EXEMPLO.read_text(encoding="utf-8")
                )
                if not isinstance(respostas_exemplo, list) or not all(
                    isinstance(item, dict) for item in respostas_exemplo
                ):
                    raise ValueError(
                        f"{ARQUIVO_EXEMPLO} deve conter uma lista JSON de objetos."
                    )

                resultado_gravacao = await sessao.call_tool(
                    "salvar_lote_respostas",
                    {"respostas": respostas_exemplo},
                )
                texto_resultado_mcp(resultado_gravacao)
                resultado_mcp = await sessao.call_tool(
                    "listar_respostas_pesquisa", {}
                )
                respostas = decodificar_respostas(
                    texto_resultado_mcp(resultado_mcp)
                )
                if not respostas:
                    raise RuntimeError(
                        "O servidor MCP não retornou respostas após salvar o lote."
                    )

            resultado_completo = app.invoke({"respostas": respostas})
            exibir_resultado(
                "EXECUÇÃO VIA SERVIDOR MCP + LANGGRAPH",
                resultado_completo,
            )

            resultado_curto = app.invoke(
                {"respostas": [{"segmento": "Serviços gerais"}]}
            )
            exibir_resultado("TESTE DE FALLBACK (AMOSTRA < MÍNIMA)", resultado_curto)


def main() -> None:
    asyncio.run(executar_pipeline_com_mcp())


if __name__ == "__main__":
    main()
