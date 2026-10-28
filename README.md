# Anima Brasil

Plataforma web para a catalogação de animações brasileiras independentes.

## Stack

- **Backend:** Python 3.14 + Django 6.1
- **Frontend:** Django Templates + Tailwind CSS (build local via Node) + JavaScript
- **Banco de dados:** PostgreSQL 16 (via Docker Compose)

## Funcionalidades

### Usuário comum (sem login)
- Visualizar o catálogo de animações
- Pesquisar e filtrar por gênero (tags), classificação indicativa ANCAINE e texto
- Usuário é **anônimo**: pode ver tudo, mas não interage

### Usuário logado
- Perfil público: nome do estúdio, descrição, avatar e links para plataformas (Instagram, YouTube, site, outros)
- Cadastrar animações no catálogo
- Comentar em animações
- Curtir (coração) e favoritar animações
- Favoritos/curtidas aparecem no perfil, com opção **público** ou **privado**
- Recebe mensagens do administrador (caixa de entrada com marcador de lida)

### Administrador
- Painel exclusivo com estatísticas (animações, usuários, pendências)
- Gerir animações: aprovar, bloquear (com motivo), desbloquear, apagar, criar/remover destaques na home
- Gerir perfis: bloquear, desbloquear, apagar, enviar mensagens
- Criar enquetes (com prazo, opções e resultados parciais) e fechar/encerrar
- Acesso ao Django Admin completo

---

## Como rodar localmente

### Pré-requisitos

| Ferramenta | Versão mínima | Verificar |
|------------|---------------|-----------|
| Python | 3.14+ | `python --version` |
| Docker Desktop | qualquer | `docker --version` |
| Node.js | 18+ | `node --version` |

### 1. Banco de dados (PostgreSQL via Docker)

```bash
docker compose up -d db
```

Isso cria o banco `animacoes_brasileiras` com usuário `postgres`/`postgres` na porta 5432. Para verificar se o container está rodando:

```bash
docker compose ps
```

### 2. Ambiente Python

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Variáveis de ambiente

Copie o `.env.example` para `.env`:

```bash
cp .env.example .env       # macOS / Linux
copy .env.example .env     # Windows (CMD)
```

Edite o `.env`:

1. **Defina `DJANGO_DEBUG=True`** para rodar em desenvolvimento.
2. **Não defina `CACHE_BACKEND`/`CACHE_LOCATION` com valores vazios** — valores
   vazios quebram a inicialização do Django. No `.env.example` essas linhas já
   vêm comentadas; em desenvolvimento o cache LocMem é usado por padrão.

Exemplo do `.env` mínimo para desenvolvimento:

```
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=qualquer-valor-para-dev-nao-precisa-ser-seguro

DB_NAME=animacoes_brasileiras
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

> Em desenvolvimento, `DJANGO_SECRET_KEY` e `DJANGO_ALLOWED_HOSTS` não são
> obrigatórios. O projeto só exige essas variáveis quando `DJANGO_DEBUG=False`.

### 4. Dependências Python

```bash
pip install -r requirements.txt
```

### 5. Estilos (Tailwind CSS)

O CSS é compilado localmente (sem CDN). Primeiro instale as dependências do Node:

```bash
npm install
```

Depois compile o CSS:

```bash
npm run build:css
```

Para desenvolvimento com recompilação automática a cada alteração:

```bash
npm run watch:css
```

### 6. Migrações e dados iniciais

```bash
python manage.py migrate
python manage.py seed_tags        # tags/gêneros pré-definidas
python manage.py seed_admin       # cria admin / admin123
python manage.py seed_demo        # opcional: dados de exemplo
```

### 7. Rodar o servidor

```bash
python manage.py runserver
```

Acesse http://127.0.0.1:8000

---

## Credenciais de desenvolvimento

| Papel | Usuário | Senha |
|-------|---------|-------|
| Administrador | `admin` | `admin123` |
| Usuário demo | `animador_demo` | `demo12345` |

## Django Admin

O Django Admin fica disponível em http://127.0.0.1:8000/admin/. Utilize as
credenciais do administrador (`admin` / `admin123`) para acessar.

## Testes

A suíte possui **68 testes** automatizados cobrindo autenticação, catálogo,
interações, moderação e páginas públicas.

```bash
python manage.py test           # roda tudo
python manage.py test accounts  # roda apenas o app accounts
```

## Estrutura do projeto

```
aplicacao_tcc/
├── config/              # settings, urls, wsgi
├── core/                # home/index
├── accounts/            # autenticação, perfil público, formulários
├── catalogo/            # animações, tags, comentários, curtidas, favoritos, destaques
│   └── management/commands/   # seed_tags, seed_admin, seed_demo
├── moderacao/           # enquetes, mensagens do admin, painel do admin
├── templates/           # templates base e compartilhados
│   ├── partials/        # card_animacao, paginacao
│   ├── accounts/
│   ├── catalogo/
│   └── moderacao/
├── static/              # css/js fontes
├── staticfiles/         # arquivos estáticos compilados (gerado por collectstatic)
├── media/               # uploads de avatar/imagem (gerado em runtime)
├── .env.example         # modelo de variáveis de ambiente
├── docker-compose.yml   # PostgreSQL via Docker
├── manage.py            # CLI do Django
├── requirements.txt     # dependências Python
├── package.json         # dependências Node (Tailwind CSS)
└── tailwind.config.js   # configuração do Tailwind
```

---

## Produção

> As instruções abaixo servem como referência. O deploy completo depende do
> ambiente de hospedagem (VPS, containers, PaaS, etc.).

### Variáveis obrigatórias

Em produção (`DJANGO_DEBUG=False`), o projeto **se recusa a iniciar** sem:

| Variável | Final |
|----------|-------|
| `DJANGO_SECRET_KEY` | Chave secreta longa e aleatória |
| `DJANGO_ALLOWED_HOSTS` | Domínio(s) do site |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origens HTTPS confiáveis |

Gere uma chave segura:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Exemplo de `.env` para produção:

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<chave gerada>
DJANGO_ALLOWED_HOSTS=animabrasil.com.br,www.animabrasil.com.br
DJANGO_CSRF_TRUSTED_ORIGINS=https://animabrasil.com.br,https://www.animabrasil.com.br
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

### Estáticos

```bash
python manage.py collectstatic --noinput
```

O WhiteNoise serve os arquivos de `staticfiles/` sem precisar de configuração
adicional no servidor web.

### Mídia (uploads)

A pasta `media/` deve ser servida pelo servidor web/proxy reverso ou por um
serviço de armazenamento de objetos (S3, etc.), pois o WhiteNoise não serve
arquivos de mídia.

### Cache

O rate limit de login utiliza o cache do Django. Com vários workers no servidor
web, defina um cache compartilhado (Redis ou Memcached) via `CACHE_BACKEND` e
`CACHE_LOCATION` no `.env`.

### Servidor WSGI

Em produção, utilize um servidor WSGI (gunicorn, uWSGI) atrás de um proxy
reverso com TLS (nginx, Caddy). **Não utilize `runserver` em produção.**

### Teste local com modo produção

Para testar `DEBUG=False` na máquina local (sem TLS), defina **ambas** as
variáveis:

```
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_HSTS_SECONDS=0
```

> **Atenção (HSTS):** com `DEBUG=False` o Django envia o header
> `Strict-Transport-Security`, e o navegador **memoriza "forçar HTTPS" para o
> host durante `DJANGO_HSTS_SECONDS` segundos** (padrão: 1 ano, valor
> `31536000`). Se você testou produção localmente sem zerar essa variável e
> depois voltou para `http://127.0.0.1:8000`, o navegador tenta HTTPS →
> `ERR_SSL_PROTOCOL_ERROR`. Em teste local use `DJANGO_HSTS_SECONDS=0`
> (desliga o HSTS). Em desenvolvimento normal (`DEBUG=True`) o HSTS **não** é
> enviado — a opção acima é só para testes que usam `DEBUG=False` na sua
> máquina.

Acesse via `http://127.0.0.1:8000`.

**Já travou no navegador?** Limpe a política HSTS do host:
- **Chrome/Edge:** abra `chrome://net-internals/#hsts` (ou `edge://net-internals/#hsts`),
  em "Delete domain security policies" digite `127.0.0.1` e clique em **Delete**.
- **Firefox:** Preferências → Privacidade e Segurança → Cookies e Dados de Sites
  → Gerenciar Dados → remova `127.0.0.1`. (Ou teste em janela anônima.)
- **Safari:** Preferências → Privacidade → Gerenciar Dados de Sites → remova.

---

## Comandos úteis

| Comando | Descrição |
|---------|-----------|
| `python manage.py runserver` | Inicia o servidor de desenvolvimento |
| `python manage.py test` | Roda a suíte de testes |
| `python manage.py check` | Verifica o projeto (configurações, models, etc.) |
| `python manage.py check --deploy` | Verifica prontidão para produção |
| `python manage.py makemigrations` | Cria migrações pendentes |
| `python manage.py migrate` | Aplica migrações ao banco |
| `python manage.py seed_tags` | Popula tags/gêneros pré-definidas |
| `python manage.py seed_admin` | Cria o administrador padrão |
| `python manage.py seed_demo` | Cria dados de exemplo |
| `python manage.py collectstatic` | Coleta arquivos estáticos para produção |
| `npm run build:css` | Compila o CSS do Tailwind (uma vez) |
| `npm run watch:css` | Compila o CSS automaticamente a cada alteração |
| `docker compose up -d db` | Inicia o PostgreSQL via Docker |
| `docker compose logs -f db` | Acompanha os logs do PostgreSQL |

---

## Troubleshooting

### Erro: `DJANGO_SECRET_KEY é obrigatória em produção`

O `.env` está com `DJANGO_DEBUG=False` (ou a variável não existe). Para
desenvolvimento local, defina `DJANGO_DEBUG=True` no `.env`.

### Erro: `Port 5432 already in use`

Outro serviço está usando a porta 5432 (provavelmente outro PostgreSQL
instalado). Soluções:
- Pare o outro serviço antes de rodar `docker compose up -d db`
- Ou mude a porta no `docker-compose.yml` (ex.: `"5433:5432"`) e atualize
  `DB_PORT=5433` no `.env`

### CSS não aplica as cores customizadas (primary, secundaria)

O arquivo `static/css/tailwind.css` não foi compilado ou está desatualizado.
Execute:

```bash
npm run build:css
```

Se não tem o Node.js instalado, veja a seção "Estilos (Tailwind CSS)" acima.

### Erro: `No directory at: .../staticfiles/`

A pasta `staticfiles/` não existe. Execute:

```bash
python manage.py collectstatic --noinput
```

### Erro CSRF ao enviar formulários

Em produção, verifique se `DJANGO_CSRF_TRUSTED_ORIGINS` está configurado com
o domínio correto (ex.: `https://animabrasil.com.br`). Em desenvolvimento,
verifique se `DJANGO_DEBUG=True`.

### Erro: O navegador força HTTPS em `http://127.0.0.1:8000` (ERR_SSL_PROTOCOL_ERROR)

Com `DJANGO_DEBUG=True` (padrão de desenvolvimento) o app **não** redireciona
para HTTPS nem envia HSTS. Se o navegador mesmo assim tentar HTTPS, ele está
obedecendo uma política HSTS antiga em cache para o host `127.0.0.1`,
geralmente gravada durante um teste local com `DEBUG=False` sem zerar
`DJANGO_HSTS_SECONDS`. Resolva:
1. Limpe o HSTS do `127.0.0.1` no navegador (ver seção
   "Teste local com modo produção").
2. Confirme que o `.env` está com `DJANGO_DEBUG=True`.
3. Reinicie o servidor: `python manage.py runserver`.

### Comando `python` não encontrado

No Windows, tente `py` ou `python3`. No macOS/Linux, use `python3` em vez de
`python`.

### Banco de dados corrompido ou em estado inconsistente

Para recriar do zero (apaga todos os dados):

```bash
docker compose down -v
docker compose up -d db
python manage.py migrate
python manage.py seed_tags
python manage.py seed_admin
python manage.py seed_demo   # opcional
```
