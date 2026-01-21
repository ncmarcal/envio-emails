import smtplib
import ssl
import csv
import time
import os
import sys
from datetime import datetime

import keyring
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SERVICE_NAME = "envio_emails_mensais"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def criar_pastas():
    pastas = ["destinatarios", "log", "documentos"]
    for pasta in pastas:
        os.makedirs(os.path.join(BASE_DIR, pasta), exist_ok=True)

def criar_arquivo_exemplo_csv():
    caminho_csv = os.path.join(BASE_DIR, "destinatarios", "emails.csv")
    if not os.path.exists(caminho_csv):
        print("📄 Arquivo 'emails.csv' não encontrado. Criando um modelo vazio...")
        with open(caminho_csv, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["email", "nome", "mensagem", "assunto", "arquivo"])
            writer.writerow(["fulano@exemplo.com", "Fulano", "Olá {nome}, segue o documento.", "Assunto de teste", "exemplo.pdf"])
        print("✅ Arquivo 'emails.csv' criado em 'destinatarios'. Preencha com seus destinatários antes de rodar novamente.")
        sys.exit(0)

def obter_credenciais():
    email_user = keyring.get_password(SERVICE_NAME, "user")
    email_pass = keyring.get_password(SERVICE_NAME, "pass")

    if email_user and email_pass:
        while True:
            resposta = input(f"Usar e-mail salvo ({email_user})? [s/n]: ").strip().lower()
            if resposta in ("s", "n"):
                break
            print("⚠️ Resposta inválida. Digite apenas 's' para Sim ou 'n' para Nao.")
        if resposta.lower() == "n":
            email_user = input("Digite o novo e-mail Gmail: ")
            email_pass = input("Digite a nova senha de app: ")
            keyring.set_password(SERVICE_NAME, "user", email_user)
            keyring.set_password(SERVICE_NAME, "pass", email_pass)
    else:
        email_user = input("Digite seu e-mail Gmail: ")
        email_pass = input("Digite sua senha de app: ")
        keyring.set_password(SERVICE_NAME, "user", email_user)
        keyring.set_password(SERVICE_NAME, "pass", email_pass)

    return email_user, email_pass

def construir_mensagem(destinatario, nome, mensagem, assunto, arquivo, email_user):
    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = destinatario
    msg["Subject"] = assunto

    corpo_personalizado = mensagem.replace("{nome}", nome)
    msg.attach(MIMEText(corpo_personalizado, "plain"))

    if arquivo:
        caminho_arquivo = os.path.join(BASE_DIR, "documentos", os.path.basename(arquivo))
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as f:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(f.read())
            encoders.encode_base64(parte)
            parte.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(caminho_arquivo)}",
            )
            msg.attach(parte)
        else:
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    return msg

def enviar_email(msg, destinatario, email_user, email_pass):
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(email_user, email_pass)
        server.sendmail(email_user, destinatario, msg.as_string())

def validar_registro(row):
    campos_obrigatorios = ["email", "nome", "mensagem", "assunto", "arquivo"]
    faltando = []

    dados = {}
    for campo in campos_obrigatorios:
        valor = (row.get(campo) or "").strip()
        dados[campo] = valor
        if not valor:
            faltando.append(campo)

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

    criar_pastas()
    criar_arquivo_exemplo_csv()

    caminho_destinatarios = os.path.join(BASE_DIR, "destinatarios", "emails.csv")

    with open(caminho_destinatarios, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            dados, erro = validar_registro(row)
            if erro:
                print(f"⚠️ Erro na linha: {row} -> {erro}")
                registrar_log(row.get("email",""), row.get("assunto",""), row.get("arquivo",""), f"ERRO: {erro}")
                continue

            try:
                msg = construir_mensagem(
                    dados["email"], dados["nome"], dados["mensagem"],
                    dados["assunto"], dados["arquivo"], EMAIL_USER
                )
                enviar_email(msg, dados["email"], EMAIL_USER, EMAIL_PASS)
                print(f"✅ Email enviado para {dados['nome']} ({dados['email']}) com anexo {dados['arquivo']}")
                registrar_log(dados["email"], dados["assunto"], dados["arquivo"], "SUCESSO")
            except Exception as e:
                print(f"❌ Falha ao enviar para {dados['nome']} ({dados['email']}): {e}")
                registrar_log(dados["email"], dados["assunto"], dados["arquivo"], f"ERRO: {e}")

            time.sleep(2)

# Executa
if __name__ == "__main__":
    processar_emails()
