import glob
import os
import google.generativeai as genai
from twitchio.ext import commands

# 1. LISTA DE CHAVES (Coloque quantas contas do Gemini quiser só seguir o padrão da lista abaixo) como conseguir as chaves? https://www.youtube.com/watch?v=eLkgX9c4EDc
CHAVES_GEMINI = [
    "",
    "",
    "",
]
TOKEN_TWITCH = "" #token do usuario/bot da twitch https://twitchtokengenerator.com - ex: oauth:123q2342423
CANAL_TWITCH = ""

#Começa por qual chave da gemini
indice_chave_atual = 0

# 2. CARREGAR A BASE DE DADOS
PASTA_DATABASE = "database"
dados_megamu = ""

arquivos_txt = glob.glob(
    os.path.join(PASTA_DATABASE, "**", "*.txt"), recursive=True
)

if not arquivos_txt:
    print(
        f"Aviso: Nenhum arquivo .txt foi encontrado dentro de '{PASTA_DATABASE}' ou suas subpastas!"
    )
else:
    print(
        f"Carregando {len(arquivos_txt)} arquivos de texto da base de dados..."
    )
    for arquivo in arquivos_txt:
        with open(arquivo, "r", encoding="utf-8") as f:
            dados_megamu += f"\n--- Arquivo: {arquivo} ---\n"
            dados_megamu += f.read() + "\n"

instrucao = f"""Você é um bot assistente do servidor MEGAMU.
Use os dados fornecidos para responder. Se a resposta não estiver nos dados, diga que não sabe.
REGRA CRÍTICA: O chat da Twitch tem limite. Responda em no MÁXIMO 300 caracteres. Seja direto.
DADOS: {dados_megamu}"""


# Função para trocar de chave e recarregar a IA
def carregar_modelo_com_chave_atual():
    global indice_chave_atual
    chave = CHAVES_GEMINI[indice_chave_atual]
    genai.configure(api_key=chave)
    return genai.GenerativeModel(
        model_name="gemini-flash-latest", system_instruction=instrucao
    )


# Inicia a IA com a primeira chave da lista
model = carregar_modelo_com_chave_atual()

# Dicionário que guarda as sessões de chat de cada usuário
# Exemplo: {"darcherman": chat_obj, "jogador2": chat_obj}
historicos_usuarios = {}


def obter_ou_criar_chat_usuario(nick):
    """Retorna o chat individual do usuário ou cria um novo se não existir."""
    if nick not in historicos_usuarios:
        historicos_usuarios[nick] = model.start_chat(history=[])
    return historicos_usuarios[nick]


def enviar_mensagem_com_rodizio(chat_ou_model, pergunta):
    """Envia a mensagem e lida com a troca de chaves se houver erro/estouro de cota."""
    global indice_chave_atual, model, historicos_usuarios

    tentativas = 0
    max_tentativas = len(CHAVES_GEMINI)

    while tentativas < max_tentativas:
        try:
            # Se for um objeto de Chat, usa send_message. Se for o modelo normal, usa generate_content.
            if hasattr(chat_ou_model, "send_message"):
                resposta = chat_ou_model.send_message(pergunta)
            else:
                resposta = chat_ou_model.generate_content(pergunta)

            return resposta.text[:400]

        except Exception as e:
            print(f"\n[Erro com Chave {indice_chave_atual + 1}]: {e}")
            tentativas += 1

            if tentativas < max_tentativas:
                indice_chave_atual = (indice_chave_atual + 1) % len(
                    CHAVES_GEMINI
                )
                print(
                    f"Trocando para a Chave {indice_chave_atual + 1} e tentando novamente..."
                )
                model = carregar_modelo_com_chave_atual()

                # Limpa os chats em memória pois o objeto do modelo mudou
                historicos_usuarios.clear()
            else:
                return "Magia falhou! Todas as chaves da IA esgotaram o limite no momento."


# 3. MODO DE TESTE VIA CONSOLE
def rodar_modo_console():
    print("\n" + "=" * 50)
    print(" MODO CONSOLE COM MEMÓRIA (Digite 'sair' para encerrar)")
    print("=" * 50)

    # Cria uma sessão de chat única para o teste do console
    chat_console = model.start_chat(history=[])

    while True:
        pergunta = input("\nVocê: ").strip()

        if pergunta.lower() in ["sair", "exit", "quit"]:
            print("Encerrando o teste no console...")
            break

        if not pergunta:
            continue

        print("Pensando...")
        resposta = enviar_mensagem_com_rodizio(chat_console, pergunta)
        print(f"Bot: {resposta}")


# 4. BOT DA TWITCH
class BotTwitch(commands.Bot):

    def __init__(self):
        super().__init__(
            token=TOKEN_TWITCH, prefix="!", initial_channels=[CANAL_TWITCH]
        )

    async def event_ready(self):
        print(
            f"\nBot Twitch ({self.nick}) ON! Usando Chave {indice_chave_atual + 1}."
        )
    
    async def event_command_error(
        self, ctx: commands.Context, error: Exception
    ):
        
        if isinstance(error, commands.CommandNotFound):
            return
        
        raise error
    
    @commands.command(name="megamu")
    async def responder_megamu(self, ctx: commands.Context):
        nick_usuario = ctx.author.name.lower()
        pergunta = ctx.message.content.replace("!megamu ", "").strip()

        if not pergunta:
            await ctx.send(
                f"@{nick_usuario}, você precisa perguntar algo! Ex: !megamu qual o lvl do reset?"
            )
            return

        print(f"[{nick_usuario}]: {pergunta}")

        # Busca o chat pessoal deste usuário específico
        chat_do_usuario = obter_ou_criar_chat_usuario(nick_usuario)

        # Processa a resposta dentro da sessão privada dele
        resposta = enviar_mensagem_com_rodizio(chat_do_usuario, pergunta)

        await ctx.send(f"@{nick_usuario} {resposta}")


# 5. SELEÇÃO DE MODO
if __name__ == "__main__":
    print("\n--- MEGAMU BOT - SELEÇÃO DE MODO ---")
    print("1 - Testar diretamente no CONSOLE (com memória)")
    print("2 - Iniciar BOT NA TWITCH (com memória individual por nick)")

    opcao = input("Escolha uma opção (1 ou 2): ").strip()

    if opcao == "1":
        rodar_modo_console()
    elif opcao == "2":
        bot = BotTwitch()
        bot.run()
    else:
        print("Opção inválida. Encerrando programa.")