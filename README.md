📧 Envio de E‑mails Mensais

Script em Python para envio automatizado de e‑mails com anexos, personalização de mensagens e registro de logs.
✨ Funcionalidades

    Envio de e‑mails via SMTP Gmail com suporte a anexos.

    Personalização de mensagens com placeholders ({nome}).

    Validação de destinatários via regex dinâmico carregado de dominios.json.

    Criação automática de ambiente:

        Pastas (destinatarios, log, documentos, img).

        Arquivo emails.csv de exemplo.

        Arquivo dominios.json com lista inicial de domínios permitidos.

    Validação de cabeçalho do CSV antes do envio.

    Armazenamento seguro de credenciais com keyring.

    Logs detalhados em log/emails.log.

📂 Estrutura de pastas
Code

.
├── destinatarios/
│   └── emails.csv
├── documentos/
│   └── anexos.pdf
├── img/
│   └── assinatura.png
├── log/
│   └── emails.log
├── dominios.json
└── envio_emails.py

⚙️ Pré‑requisitos

    Python 3.9+

    Bibliotecas: smtplib, ssl, csv, json, keyring

    Conta Gmail com senha de app habilitada

🚀 Como usar

A priemeira maneira é através do executável do script estará na aba de releases

A segunda maneira está logo abaixo:

    1. Clone ou copie o projeto.

    2. Instale dependências:
        pip install keyring

    3. Execute o script:
        python envio_emails.py

    4. Na primeira execução:

        Será criado emails.csv de exemplo em destinatarios/.

        Edite esse arquivo com seus destinatários.

        Adicione anexos em documentos/.

        Coloque sua assinatura em img/assinatura.png.

    5. O script solicitará seu e‑mail Gmail e senha de app.

        As credenciais serão salvas com segurança via keyring.

📊 Logs

Cada envio gera uma linha em log/emails.log com:
Code

datahora,destinatario,assunto,arquivo,status
