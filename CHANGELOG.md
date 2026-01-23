📦 Versão 1.0.0 — Envio de E‑mails Mensais ✨ Novidades

    Envio automatizado de e‑mails com suporte a anexos e assinatura em HTML.

    Personalização de mensagens com placeholders ({nome}) substituídos dinamicamente.

    Validação de destinatários via regex dinâmico, carregado de dominios.json.

    Criação automática de ambiente:

        Pastas (destinatarios, log, documentos, img).

        Arquivo emails.csv de exemplo, se não existir.

        Arquivo dominios.json com lista inicial de domínios permitidos.

    Validação de cabeçalho do CSV para garantir consistência dos dados.

    Armazenamento seguro de credenciais usando keyring.

    Logs detalhados em emails.log com status de cada envio.

    Lazy loading do regex para eficiência e robustez.

🛠️ Melhorias técnicas

    Separação clara de responsabilidades:

        montar_ambiente() → prepara e valida ambiente.

        processar_emails() → obtém credenciais e envia.

    Tratamento de erros SMTP diferenciado (autenticação, conexão, destinatário recusado).

    Intervalo entre envios (time.sleep(2)) para evitar bloqueios.

📌 Roadmap futuro

    Configuração externa (config.json ou .ini) para servidor, intervalo e parâmetros.

    Intervalo entre envios parametrizável.

    Logs estruturados com o módulo logging.

    Placeholders adicionais além de {nome} (ex.: {assunto}, {data}).

    Validação antecipada de anexos listados no CSV.

    Testes unitários para funções isoladas.

    Interface web.
    
    Aceitar outros servidores (dominio do autenticado) de email alem do gmail.