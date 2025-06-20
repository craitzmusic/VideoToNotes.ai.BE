# VideoToNotes.ai - Guia Completo de Configuração e Uso

Este documento detalha passo a passo como configurar, executar e utilizar o projeto VideoToNotes.ai,  
que faz transcrição de áudio/vídeo usando Whisper localmente e FastAPI para a API,  
com resumo automático via modelos LLM rodando localmente pelo Ollama.

---

## 1. Pré-requisitos

- Python 3.12 instalado (ou superior)  
- Docker e Docker Compose instalados (recomendado para evitar poluição do sistema)  
- git instalado (para clonar o repositório)  
- FFmpeg instalado (se não usar Docker)  
- (Opcional) Homebrew para instalar dependências no Mac/Linux, se não usar Docker  
- Pelo menos 6 GB de RAM livres se for usar modelos LLM via Ollama  
- Modelos compatíveis com seu hardware (ex: llama3, phi3, gemma)

---

## 2. Clonando o projeto

1. Clone o repositório (substitua a URL pelo do seu projeto):

    git clone https://github.com/seuusuario/VideoToNotes.ai.git
    cd VideoToNotes.ai

---

## 3. Configuração do ambiente virtual (sem Docker)

1. Crie o ambiente virtual python:

        python3 -m venv venv

2. Ative o ambiente virtual:

    No Linux/macOS:

        source venv/bin/activate

    No Windows:

        venv\Scripts\activate

3. Instale as dependências do requirements.txt:

    pip install -r requirements.txt

4. Crie o arquivo `.env` baseado no `.env.example` e configure suas variáveis (ex: API_KEYS, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME)

---

## 4. Rodando localmente (sem Docker)

1. Certifique-se que o ambiente virtual está ativo.  
2. Execute o app com uvicorn:

    uvicorn app.main:app --reload

3. O servidor estará rodando em:

    http://127.0.0.1:8000

4. Para transcrever um áudio, use o endpoint POST `/transcribe` (exemplo via curl ou Postman)

5. Certifique-se que o Ollama está rodando localmente e com o modelo configurado (ex: llama3).  
   Exemplo para rodar um modelo leve:

    ollama pull llama3  
    ollama run llama3

---

## 5. Usando Docker (recomendado para ambiente profissional)

1. No diretório raiz, já deve existir o Dockerfile e docker-compose.yml configurados.  
2. Para buildar e subir o container:

    docker-compose up --build

3. O app ficará disponível em:

    http://localhost:8000

4. Para parar o container, use:

    docker-compose down

---

## 6. Notas importantes e dicas

- O projeto usa o modelo Whisper para transcrição local (não usa API externa OpenAI).  
- É necessário o FFmpeg instalado para processar áudio (no Docker já está instalado).  
- O arquivo `.env` é usado para guardar variáveis de ambiente (ex: chaves, configs, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME).  
- Use o Docker para evitar instalação local do FFmpeg e outras dependências.  
- Caso rode localmente, instale FFmpeg pelo Homebrew (macOS):

    brew install ffmpeg

  Se não puder instalar, prefira usar Docker.

- Para uploads grandes, configure o servidor e client para aceitar arquivos maiores.  
- Para desenvolvimento, `uvicorn --reload` reinicia o servidor ao mudar o código.  
- Se ocorrer erro de modelo no Ollama dizendo "model requires more system memory", tente usar um modelo menor, como `llama3`, `phi3` ou `gemma`.  
- Caso o resumo retorne erro 500, verifique se o Ollama está rodando e o modelo está carregado.  
- Arquivos temporários são limpos automaticamente após processamento.  
- O Whisper está configurado para o modelo "base" por padrão, pode ser alterado no código.  
- Para transcrição de vídeos, o áudio é extraído automaticamente via ffmpeg.

---

## 7. Estrutura do projeto

    /app
      /main.py           # aplicação FastAPI principal
      /routers           # endpoints API (se separar depois)
      /services          # lógica de transcrição e resumo (se refatorar)
      /models            # schemas Pydantic (se separar depois)
    Dockerfile           # configura container docker
    docker-compose.yml   # orquestra container com volumes e portas
    requirements.txt     # dependências python
    .env.example         # exemplo de variáveis ambiente

---

## 8. Exemplos de uso (curl)

Transcrever áudio ou vídeo via curl (substitua arquivo.mp3 pelo seu arquivo):

    curl -X POST "http://localhost:8000/transcribe" -F "file=@arquivo.mp3"

Transcrever áudio de vídeo do YouTube:

    curl -X POST "http://localhost:8000/transcribe_youtube" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.youtube.com/watch?v=ABC123"}'

---

## 9. Problemas comuns e soluções

- Erro 'python-multipart' não instalado:  

    pip install python-multipart

- Erro SSL certificado:  
  Pode ser problema local, ignore para localhost ou configure certificados.

- Erro 'ffmpeg not found':  
  Instale ffmpeg ou rode via Docker.

- Erro 'AttributeError whisper.load_model':  
  Certifique-se de instalar a biblioteca correta:  

    pip install openai-whisper

- Erro "model requires more system memory" na geração de resumo:  
  Use um modelo LLM mais leve, ex: `llama3`, `phi3`, `gemma`.

- Erro 500 na API de resumo:  
  Verifique se o Ollama está rodando e o modelo carregado corretamente.

---

## 10. Próximos passos para aprimoramento

- Adicionar autenticação na API  
- Implementar front-end web  
- Melhorar tratamento de erros e logging  
- Adicionar suporte para mais idiomas e modelos  
- Upload progressivo e feedback via WebSocket

---

## Contato

Projeto desenvolvido por Camilo Raitz - Adaptado para VideoToNotes.ai  
Email: craitz@gmail.com  
GitHub: https://github.com/craitz

---

Fim do documento.