import google.generativeai as genai

# Coloque suas chaves aqui para testar
CHAVES_GEMINI = [
    "",
    "",
    "",
]

for i, chave in enumerate(CHAVES_GEMINI):
    print(f"\n==========================================")
    print(f"VERIFICANDO CHAVE {i + 1}")
    print(f"==========================================")
    try:
        genai.configure(api_key=chave)

        # Busca todos os modelos suportados pela chave
        modelos_disponiveis = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                modelos_disponiveis.append(m.name)

        if modelos_disponiveis:
            print("Modelos liberados para uso:")
            for m in modelos_disponiveis:
                # Remove o prefixo 'models/' para facilitar a leitura
                nome_limpo = m.replace("models/", "")
                print(f"  - {nome_limpo}")
        else:
            print("Nenhum modelo com suporte a 'generateContent' foi encontrado.")

    except Exception as e:
        print(f"Erro ao verificar a chave {i + 1}: {e}")