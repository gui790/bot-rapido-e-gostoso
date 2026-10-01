import os
import httpx
from fastapi import FastAPI, Request, Response
from google import genai

app = FastAPI()

# Suas credenciais
GEMINI_API_KEY = "SUA_CHAVE_DO_GOOGLE_STUDIO"  AQ.Ab8RN6LrJbk-a4dhFAq5UGe3kqV5RZ3ZjIDBypIYuCK374Ei9w
WHATSAPP_TOKEN = "EAAX5E4EptvoBSuPiBmnlSz55AZCF8iz45EXkxAduh8s7SmSyGB4Y9vMLi43lR9ZChjqiqO33FisvKhpjVL4cQUBHuw78WX9DSd8dQ5f5WcWso0fZAzOeZCLlDSAzh5AOTxhCIxeW3gSxMsZBLbb6EYfZCkJGDjPF54wUcAfXMvPgYljCkHBgMEaVFsiVQNp6iyOtpdBeZCQZA7hQ9csXNuplltm3oJbJ6AP75Htf4ZBflr1ZAFtxNPWMpN3ihJZC6ilzNOKPEMq4FJi5w73it1lwBmy"
PHONE_NUMBER_ID = "SEU_PHONE_NUMBER_ID_AQUI"  1313037015228657
VERIFY_TOKEN = "rapido_e_gostoso_token"

ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Você é o assistente virtual de atendimento e vendas do "Rápido & Gostoso - Salgados e Doces", fundado pela família Vieira.
Seu objetivo é ser atencioso, ágil, acolhedor e focado em encantar o cliente.

Você deve:
1. Tirar dúvidas sobre o cardápio, ingredientes e recomendações.
2. Auxiliar nas escolhas (combos, festas, lanches rápidos).
3. Coletar os dados para fechamento do pedido caso o cliente queira pedir.

CARDÁPIO DA CASA:
- Mini Salgados (porções / centos / copos):
  * Mini Coxinha (frango tradicional cremoso)
  * Mini Bolinha de Queijo
  * Mini Bolinha de Calabresa
  * Mini Presunto e Queijo
  * Mini Salsicha (enroladinho)
- Salgados Grandes:
  * Coxinha Tradicional Grande
  * Bolinha de Queijo Grande
  * Presunto e Queijo Grande
- Porções Especiais:
  * Batata Frita crocante
  * Batata Sorriso
  * Nuggets de frango
- Doces:
  * Mini Churros (Doce de Leite / Chocolate)
- Bebidas: Refrigerantes (Coca-Cola normal/Zero, Guaraná), Sucos e Água.

ÁREA DE ATENDIMENTO E REGRAS:
- Região: Nova Odessa, Sumaré e cidades vizinhas.
- Modos: Entrega (Delivery) ou Retirada no balcão.
- Pagamento: Pix, Cartão de Crédito/Débito ou Dinheiro.

ETAPAS PARA FECHAR O PEDIDO:
Quando o cliente demonstrar que quer pedir:
1. Confirme os itens e quantidades.
2. Pergunte se é Entrega ou Retirada.
3. Se for entrega, peça o Endereço completo (Rua, Número, Bairro e Cidade).
4. Peça o Nome do cliente.
5. Pergunte a Forma de pagamento (se for dinheiro, confirme se precisa de troco).
6. Apresente um resumo final organizado para o cliente confirmar.

Mantenha respostas curtas e fáceis de ler no WhatsApp (use negrito e emojis moderados).
"""

chat_histories = {}

async def send_whatsapp_message(to_number: str, text: str):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Verificação falhou", status_code=403)

@app.post("/webhook")
async def handle_whatsapp_message(request: Request):
    data = await request.json()
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            message_obj = entry["messages"][0]
            from_number = message_obj["from"]
            user_text = message_obj.get("text", {}).get("body", "")

            if user_text:
                if from_number not in chat_histories:
                    chat_histories[from_number] = []

                history = chat_histories[from_number]
                history.append(f"Cliente: {user_text}")

                recent_history = history[-10:]
                prompt = f"{SYSTEM_PROMPT}\n\nHistórico:\n" + "\n".join(recent_history) + "\n\nAssistente:"

                response = ai_client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )
                bot_reply = response.text.strip()
                history.append(f"Assistente: {bot_reply}")

                await send_whatsapp_message(from_number, bot_reply)
    except Exception as e:
        print(f"Erro: {e}")
    return {"status": "ok"}
