from collections import Counter
from typing import Any, Dict, List, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

AMOSTRA_MINIMA = 3


class PesquisaState(TypedDict, total=False):
    respostas: List[Dict[str, Any]]
    total_respostas: int
    amostra_suficiente: bool
    segmento_foco: str
    dor_principal: str
    promessa_unica: str
    mensagem_whatsapp: str
    status_execucao: str


def consolidar_dados(state: PesquisaState) -> PesquisaState:
    """Conta as respostas e verifica se a amostra mínima foi atingida."""
    total = len(state.get("respostas", []))
    return {
        **state,
        "total_respostas": total,
        "amostra_suficiente": total >= AMOSTRA_MINIMA,
    }


def decidir_proximo_passo(
    state: PesquisaState,
) -> Literal["analisar_padroes", "gerar_alerta_coleta"]:
    """Escolhe o ramo de análise ou o alerta de coleta."""
    if state.get("amostra_suficiente", False):
        return "analisar_padroes"
    return "gerar_alerta_coleta"


def gerar_alerta_coleta(state: PesquisaState) -> PesquisaState:
    """Retorna uma orientação quando ainda faltam respostas."""
    total = state.get("total_respostas", 0)
    faltam = AMOSTRA_MINIMA - total
    return {
        **state,
        "segmento_foco": "Aguardando amostra mínima",
        "dor_principal": "Dados insuficientes para validar um padrão com segurança",
        "promessa_unica": "Continue a coleta antes de definir a oferta.",
        "mensagem_whatsapp": (
            f"Ação necessária: colete mais {faltam} resposta(s) no link "
            "https://surveymars.com/q/NQ0mP7VBi para atingir o mínimo de "
            f"{AMOSTRA_MINIMA} respostas."
        ),
        "status_execucao": f"COLETA_INSUFICIENTE ({total}/{AMOSTRA_MINIMA})",
    }


def _valor_resposta(resposta: Dict[str, Any], campo: str, padrao: str) -> str:
    valor = resposta.get(campo)
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    return padrao


def analisar_padroes(state: PesquisaState) -> PesquisaState:
    """Identifica o segmento e a dor mais frequentes."""
    respostas = state.get("respostas", [])
    segmentos = [
        _valor_resposta(resposta, "segmento", "Pequenos negócios")
        for resposta in respostas
    ]
    dores = [
        _valor_resposta(
            resposta,
            "dor_relatada",
            "Falta de clareza sobre entradas, saídas e lucro real",
        )
        for resposta in respostas
    ]

    return {
        **state,
        "segmento_foco": Counter(segmentos).most_common(1)[0][0],
        "dor_principal": Counter(dores).most_common(1)[0][0],
    }


def gerar_posicionamento(state: PesquisaState) -> PesquisaState:
    """Gera uma promessa e uma mensagem a partir dos padrões identificados."""
    segmento = state["segmento_foco"]
    dor = state["dor_principal"]

    promessa = (
        f"Para {segmento}: tenha clareza semanal do que entra, sai e sobra no "
        f"seu negócio, enfrentando {dor.lower()} sem depender de planilhas "
        "complicadas ou sistemas difíceis."
    )
    mensagem_whatsapp = (
        f"Olá! Ajudo donos de {segmento} a lidar com {dor.lower()} por meio de "
        "um controle simples e acompanhado. Posso te mostrar em 2 minutos "
        "como funciona na prática?"
    )

    return {
        **state,
        "promessa_unica": promessa,
        "mensagem_whatsapp": mensagem_whatsapp,
        "status_execucao": (
            f"CONCLUIDO_COM_SUCESSO ({state['total_respostas']} respostas analisadas)"
        ),
    }


def build_graph():
    builder = StateGraph(PesquisaState)
    builder.add_node("consolidar_dados", consolidar_dados)
    builder.add_node("gerar_alerta_coleta", gerar_alerta_coleta)
    builder.add_node("analisar_padroes", analisar_padroes)
    builder.add_node("gerar_posicionamento", gerar_posicionamento)

    builder.add_edge(START, "consolidar_dados")
    builder.add_conditional_edges(
        "consolidar_dados",
        decidir_proximo_passo,
        {
            "analisar_padroes": "analisar_padroes",
            "gerar_alerta_coleta": "gerar_alerta_coleta",
        },
    )
    builder.add_edge("gerar_alerta_coleta", END)
    builder.add_edge("analisar_padroes", "gerar_posicionamento")
    builder.add_edge("gerar_posicionamento", END)
    return builder.compile()
