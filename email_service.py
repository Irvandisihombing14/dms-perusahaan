"""
Modul Email Service - DMS PNS
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import get_email_config


def send_email(recipient_email, subject, html_body, attachment_path=None, attachment_name=None):
    config = get_email_config()
    if not config["SENDER_EMAIL"] or not config["SENDER_PASSWORD"]:
        return False, "Konfigurasi email belum diset!"
    try:
        msg = MIMEMultipart()
        msg['From'] = config["SENDER_EMAIL"]
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        if attachment_path and attachment_name:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_name}"')
            msg.attach(part)
        server = smtplib.SMTP(config["SMTP_SERVER"], config["SMTP_PORT"])
        server.starttls()
        server.login(config["SENDER_EMAIL"], config["SENDER_PASSWORD"])
        server.send_message(msg)
        server.quit()
        return True, "Email berhasil dikirim!"
    except smtplib.SMTPAuthenticationError:
        return False, "Autentikasi SMTP gagal! Periksa App Password."
    except Exception as e:
        return False, f"Error: {str(e)}"


def send_pdf_email(recipient_email, pdf_filepath, pdf_filename, uploader_name, doc_title):
    config = get_email_config()
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #1e3a8a;">🏛️ {config['APP_NAME']}</h2>
            <hr style="border: 1px solid #eee;">
            <p>Halo,</p>
            <p>Dokumen administrasi PNS baru telah diunggah:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; background: #f9f9f9; font-weight: bold;">Judul:</td>
                    <td style="padding: 8px;">{doc_title}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background: #f9f9f9; font-weight: bold;">File:</td>
                    <td style="padding: 8px;">{pdf_filename}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background: #f9f9f9; font-weight: bold;">Pengunggah:</td>
                    <td style="padding: 8px;">{uploader_name}</td>
                </tr>
            </table>
            <p><strong>📎 Dokumen terlampir dalam email ini.</strong></p>
            <hr style="border: 1px solid #eee;">
            <p style="font-size: 12px; color: #888;">Email otomatis dari {config['APP_NAME']}.</p>
        </div>
    </body>
    </html>
    """
    return send_email(recipient_email, f"📄 Dokumen Baru: {doc_title}", html_body, pdf_filepath, pdf_filename)


def send_approval_notification(recipient_email, doc_title, status, approver_name="", reason=""):
    config = get_email_config()
    if status == "approved":
        subject = f"✅ Dokumen Disetujui: {doc_title}"
        html_body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #28a745;">✅ Dokumen Disetujui</h2>
            <p>Halo,</p>
            <p>Dokumen <strong>{doc_title}</strong> telah <strong>disetujui</strong> oleh {approver_name}.</p>
            <p style="font-size: 12px; color: #888;">Email otomatis dari {config['APP_NAME']}.</p>
        </div></body></html>
        """
    else:
        subject = f"❌ Dokumen Ditolak: {doc_title}"
        html_body = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #dc3545;">❌ Dokumen Ditolak</h2>
            <p>Halo,</p>
            <p>Dokumen <strong>{doc_title}</strong> telah <strong>ditolak</strong> oleh {approver_name}.</p>
            <p><strong>Alasan:</strong> {reason}</p>
            <p style="font-size: 12px; color: #888;">Email otomatis dari {config['APP_NAME']}.</p>
        </div></body></html>
        """
    return send_email(recipient_email, subject, html_body)