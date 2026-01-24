import json
import smtplib
import ssl
import csv
import time
import os
import sys
import re
from datetime import datetime

import keyring
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.image import MIMEImage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SERVICE_NAME = "envio_emails_mensais"
REGEX_DOMINIOS = None

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def criar_pastas():
    pastas = ["destinatarios", "log", "documentos", "img"]
    for pasta in pastas:
        os.makedirs(os.path.join(BASE_DIR, pasta), exist_ok=True)

def criar_arquivo_dominios_json():
    caminho_json = os.path.join(BASE_DIR, "dominios.json")
    if not os.path.exists(caminho_json):
        dominios_iniciais = {
            "dominios_permitidos": [
                "gmail.com",
                "hotmail.com",
                "outlook.com",
                "yahoo.com",
                "protonmail.com",
                "icloud.com",
                "live.com",
                "empresa.com",
                "empresa.org",
                "empresa.com.br",
                "empresa.org.br"
            ]
        }
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(dominios_iniciais, f, indent=4, ensure_ascii=False)
        print("✅ Arquivo 'dominios.json' criado com domínios padrão.")

def carregar_regex_dominios():
    caminho = os.path.join(BASE_DIR, "dominios.json")
    with open(caminho, "r", encoding="utf-8") as f:
        data = json.load(f)
    dominios = data["dominios_permitidos"]

    grupo_dominios = "|".join([re.escape(d) for d in dominios])
    padrao = rf'^[A-Za-z0-9._%+-]+@({grupo_dominios})$'
    return re.compile(padrao)

def validar_email_destinatario(email: str) -> bool:
    global REGEX_DOMINIOS
    if REGEX_DOMINIOS is None:
        criar_arquivo_dominios_json()
        REGEX_DOMINIOS = carregar_regex_dominios()
    return REGEX_DOMINIOS.fullmatch(email.strip()) is not None

def criar_arquivo_exemplo_csv():
    caminho_csv = os.path.join(BASE_DIR, "destinatarios", "emails.csv")
    if not os.path.exists(caminho_csv):
        print("📄 Arquivo 'emails.csv' não encontrado. Criando um modelo vazio...")
        with open(caminho_csv, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["email", "nome", "mensagem", "assunto", "arquivo"])
            writer.writerow([
                "exemplo@exemplo.com",
                "Fulano",
                "Olá {nome}, segue o documento.",
                "Assunto de teste",
                "exemplo.pdf"
            ])
        print("✅ Arquivo 'emails.csv' criado em 'destinatarios'. Preencha com seus destinatários antes de rodar novamente.")
        sys.exit(0)

def validar_cabecalho_csv(caminho_csv):
    campos_obrigatorios = ["email", "nome", "mensagem", "assunto", "arquivo"]

    with open(caminho_csv, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        cabecalho = reader.fieldnames

        if not cabecalho:
            raise ValueError("⚠️ CSV vazio ou sem cabeçalho.")

        faltando = [campo for campo in campos_obrigatorios if campo not in cabecalho]
        extras = [campo for campo in cabecalho if campo not in campos_obrigatorios]

        if faltando:
            raise ValueError(f"⚠️ Cabeçalho inválido. Faltam colunas: {faltando}")
        if extras:
            print(f"ℹ️ Aviso: colunas extras encontradas no CSV: {extras}")

    print("✅ Cabeçalho do CSV validado com sucesso.")

def montar_ambiente():
    caminho_destinatarios_csv = os.path.join(BASE_DIR, "destinatarios", "emails.csv")
    criar_pastas()
    criar_arquivo_exemplo_csv()
    validar_cabecalho_csv(caminho_destinatarios_csv)

def obter_credenciais():
    email_user = keyring.get_password(SERVICE_NAME, "user")
    email_pass = keyring.get_password(SERVICE_NAME, "pass")

    if email_user and email_pass:
        while True:
            resposta = input(f"Usar e-mail salvo ({email_user})? [s/n]: ").strip().lower()
            if resposta in ("s", "n"):
                break
            print("⚠️ Resposta inválida. Digite apenas 's' para Sim ou 'n' para Nao.")
        if resposta == "n":
            email_user, email_pass = solicitar_novas_credenciais()
    else:
        email_user, email_pass = solicitar_novas_credenciais()

    return email_user, email_pass

def solicitar_novas_credenciais():
    while True:
        email_user = input("Digite seu e-mail Gmail: ").strip()
        if not re.fullmatch(r'^[A-Za-z0-9._%+-]+@gmail\.com$', email_user):
            print("⚠️ Apenas endereços @gmail.com são aceitos. Tente novamente.")
            continue
        break

    email_pass = input("Digite sua senha de app: ").strip()
    keyring.set_password(SERVICE_NAME, "user", email_user)
    keyring.set_password(SERVICE_NAME, "pass", email_pass)
    return email_user, email_pass


def montar_corpo_html(mensagem, nome):
    corpo_personalizado = mensagem.replace("{nome}", nome)
    html = f"""
    <html>
      <body>
        <p>{corpo_personalizado}</p>
        <br>
        <img src="cid:assinatura_img" alt="Assinatura" style="width:200px;">
      </body>
    </html>
    """
    return corpo_personalizado, html

def adicionar_anexos(msg, arquivos):
    lista_arquivos = [a.strip() for a in arquivos.split(",") if a.strip()]
    for arquivo in lista_arquivos:
        caminho_arquivo = os.path.join(BASE_DIR, "documentos", os.path.basename(arquivo))
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        with open(caminho_arquivo, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(caminho_arquivo)}")
        msg.attach(parte)

def adicionar_assinatura(msg):
    caminho_assinatura = os.path.join(BASE_DIR, "img", "assinatura.png")
    if not os.path.exists(caminho_assinatura):
        raise FileNotFoundError(f"Imagem de assinatura não encontrada em: {caminho_assinatura}")
    with open(caminho_assinatura, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", "<assinatura_img>")
        img.add_header("Content-Disposition", "inline", filename="assinatura.png")
        msg.attach(img)

def construir_mensagem(destinatario, nome, mensagem, assunto, arquivos, email_user):
    msg = MIMEMultipart("related")
    msg["From"] = email_user
    msg["To"] = destinatario
    msg["Subject"] = assunto

    msg_alternativo = MIMEMultipart("alternative")
    msg.attach(msg_alternativo)

    corpo_texto, corpo_html = montar_corpo_html(mensagem, nome)
    msg_alternativo.attach(MIMEText(corpo_texto, "plain"))
    msg_alternativo.attach(MIMEText(corpo_html, "html"))

    adicionar_anexos(msg, arquivos)
    adicionar_assinatura(msg)

    return msg

def enviar_email(msg, destinatario, email_user, email_pass):
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(email_user, email_pass)
            server.sendmail(email_user, destinatario, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        raise Exception("Erro de autenticação: verifique usuário e senha de app.")
    except smtplib.SMTPConnectError:
        raise Exception("Erro de conexão com o servidor SMTP.")
    except smtplib.SMTPRecipientsRefused:
        raise Exception(f"Destinatário recusado: {destinatario}")
    except smtplib.SMTPException as e:
        raise Exception(f"Erro SMTP genérico: {e}")

def validar_registro(row):
    campos_obrigatorios = ["email", "nome", "mensagem", "assunto", "arquivo"]
    faltando = []
    dados = {}
    for campo in campos_obrigatorios:
        valor = (row.get(campo) or "").strip()
        dados[campo] = valor
        if not valor:
            faltando.append(campo)

    if not faltando and not validar_email_destinatario(dados["email"]):
        faltando.append("email inválido")

    if faltando:
        return None, faltando
    return dados, None

def registrar_log(destinatario, assunto, arquivo, status):
    datahoje = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    caminho_log = os.path.join(BASE_DIR, "log", "emails.log")
    with open(caminho_log, "a", encoding="utf-8") as log:
        log.write(f"{datahoje},{destinatario},{assunto},{arquivo},{status}\n")

def processar_emails():
    EMAIL_USER, EMAIL_PASS = obter_credenciais()
    montar_ambiente()

    caminho_destinatarios = os.path.join(BASE_DIR, "destinatarios", "emails.csv")
    total_sucesso, total_erros = 0, 0

    with open(caminho_destinatarios, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            dados, erro = validar_registro(row)
            if erro:
                print(f"⚠️ Erro na linha: {row} -> {erro}")
                registrar_log(row.get("email",""), row.get("assunto",""), row.get("arquivo",""), f"ERRO: {erro}")
                total_erros += 1
                continue

            try:
                msg = construir_mensagem(
                    dados["email"], dados["nome"], dados["mensagem"],
                    dados["assunto"], dados["arquivo"], EMAIL_USER
                )
                enviar_email(msg, dados["email"], EMAIL_USER, EMAIL_PASS)
                print(f"✅ Email enviado para {dados['nome']} ({dados['email']}) com anexo {dados['arquivo']}")
                registrar_log(dados["email"], dados["assunto"], dados["arquivo"], "SUCESSO")
                total_sucesso += 1
            except Exception as e:
                print(f"❌ Falha ao enviar para {dados['nome']} ({dados['email']}): {e}")
                registrar_log(dados["email"], dados["assunto"], dados["arquivo"], f"ERRO: {e}")
                total_erros += 1

            time.sleep(2)

    print(f"\n📊 Resumo: {total_sucesso} enviados com sucesso, {total_erros} falharam.")

if __name__ == "__main__":
    processar_emails()
