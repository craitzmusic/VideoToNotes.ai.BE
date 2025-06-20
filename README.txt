VideoToNotes.ai - Guia Completo de Configuração e Uso
=====================================================

Este documento detalha passo a passo como configurar, executar e utilizar o projeto VideoToNotes.ai,
que faz transcrição de áudio/video usando Whisper localmente e FastAPI para a API.

-----------------------------------------------------------------------------------------
1. Pré-requisitos
-----------------------------------------------------------------------------------------

- Python 3.12 instalado (ou superior)
- Docker e Docker Compose instalados (recomendado para evitar poluição do sistema)
- git instalado (para clonar o repositório)
- (Opcional) Homebrew para instalar dependências no Mac/Linux, se não usar Docker

-----------------------------------------------------------------------------------------
2. Clonando o projeto
-----------------------------------------------------------------------------------------

1. Clone o repositório (substitua a URL pelo do seu projeto):

   git clone https://github.com/seuusuario/VideoToNotes.ai.git
   cd VideoToNotes.ai

-----------------------------------------------------------------------------------------
3. Configuração do ambiente virtual (sem Docker)
-----------------------------------------------------------------------------------------

1. Crie o ambiente virtual python:

   python3 -m venv venv

2. Ative o ambiente virtual:

   No Linux/macOS:
   source venv/bin/activate

   No Windows:
   venv\Scripts\activate

3. Instale as dependências do requirements.txt:

   pip install -r requirements.txt

4. Crie o arquivo `.env` baseado no `.env.example` e configure suas variáveis (ex: API_KEYS, etc)

-----------------------------------------------------------------------------------------
4. Rodando localmente (sem Docker)
-----------------------------------------------------------------------------------------

1. Certifique-se que o ambiente virtual está ativo.
2. Execute o app com uvicorn:

   uvicorn app.main:app --reload

3. O servidor estará rodando em:

   http://127.0.0.1:8000

4. Para transcrever um áudio, use o endpoint POST /transcribe (exemplo via curl ou Postman)

-----------------------------------------------------------------------------------------
5. Usando Docker (recomendado para ambiente profissional)
-----------------------------------------------------------------------------------------

1. No diretório raiz, já deve existir o Dockerfile e docker-compose.yml configurados.
2. Para buildar e subir o container:

   docker-compose up --build

3. O app ficará disponível em:

   http://localhost:8000

4. Para parar o container, use:

   docker-compose down

-----------------------------------------------------------------------------------------
6. Notas importantes e dicas
-----------------------------------------------------------------------------------------

- O projeto usa o modelo Whisper para transcrição local (não usa API externa OpenAI).
- É necessário o FFmpeg instalado para processar áudio (no Docker já está instalado).
- O arquivo `.env` é usado para guardar variáveis de ambiente (ex: chaves, configs).
- Use o Docker para não precisar instalar FFmpeg e dependências no seu sistema local.
- Caso rode localmente, instale FFmpeg pelo Homebrew (macOS):

  brew install ffmpeg

  Se não puder instalar, prefira usar Docker.

- Para uploads grandes, configure o servidor e client para aceitar arquivos maiores.
- Para desenvolvimento, `uvicorn --reload` reinicia o servidor ao mudar o código.

-----------------------------------------------------------------------------------------
7. Estrutura do projeto
-----------------------------------------------------------------------------------------

/app
  /main.py           # aplicação FastAPI principal
  /routers           # endpoints API
  /services          # lógica de transcrição e processamento
  /models            # schemas Pydantic
Dockerfile           # configura container docker
docker-compose.yml   # orquestra container com volumes e portas
requirements.txt     # dependências python
.env.example         # exemplo de variáveis ambiente

-----------------------------------------------------------------------------------------
8. Exemplos de uso (curl)
-----------------------------------------------------------------------------------------

Transcrever áudio via curl (substitua arquivo.mp3 pelo seu arquivo):

curl -X POST "http://localhost:8000/transcribe" -F "file=@arquivo.mp3"

-----------------------------------------------------------------------------------------
9. Problemas comuns e soluções
-----------------------------------------------------------------------------------------

- Erro 'python-multipart' não instalado:
  pip install python-multipart

- Erro SSL certificado:
  Pode ser problema local, ignore para localhost ou configure certificados.

- Erro 'ffmpeg not found':
  Instale ffmpeg ou rode via Docker.

- Erro 'AttributeError whisper.load_model':
  Certifique-se de instalar a biblioteca correta: `pip install openai-whisper`

-----------------------------------------------------------------------------------------
10. Próximos passos para aprimoramento
-----------------------------------------------------------------------------------------

- Adicionar autenticação na API
- Implementar front-end web
- Melhorar tratamento de erros e logging
- Adicionar suporte para mais idiomas e modelos

-----------------------------------------------------------------------------------------
Contato
-----------------------------------------------------------------------------------------

Projeto desenvolvido por Camilo Raitz - Adaptado para VideoToNotes.ai  
Email: craitz@gmail.com
GitHub: https://github.com/craitz

---

Fim do documento.