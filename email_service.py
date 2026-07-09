"""
Modul Email Service - Mengirim email dengan attachment PDF
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import get_email_config


def send_pdf_email(recipient_email, pdf_filepath, pdf_filename,
                   uploader_name, doc_title):
    """
    Kirim email dengan attachment PDF

    Returns:
        tuple: (success: bool, message: str)
    """
    config = get_email_config()

    if not config["SENDER_EMAIL"] or not config["SENDER_PASSWORD"]:
        return False, "Konfigurasi email belum diset!"

    try:
        msg = MIMEMultipart()
        msg['From'] = config["SENDER_EMAIL"]
        msg['To'] = recipient_email
        msg['Subject'] = f"📄 Dokumen Baru: {doc_title}"

        # Body email HTML
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;
                        border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #FF4B4B;">📂 {config['APP_NAME']}</h2>
                <hr style="border: 1px solid #eee;">

                <p>Halo,</p>

                <p>Dokumen baru telah berhasil diunggah ke sistem:</p>

                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; background: #f9f9f9; font-weight: bold;">
                            Judul Dokumen:
                        </td>
                        <td style="padding: 8px;">{doc_title}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f9f9f9; font-weight: bold;">
                            Nama File:
                        </td>
                        <td style="padding: 8px;">{pdf_filename}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f9f9f9; font-weight: bold;">
                            Diunggah oleh:
                        </td>
                        <td style="padding: 8px;">{uploader_name}</td>
                    </tr>
                </table>

                <p><strong>📎 Dokumen terlampir dalam email ini.</strong></p>

                <hr style="border: 1px solid #eee;">
                <p style="font-size: 12px; color: #888;">
                    Email ini dikirim otomatis oleh {config['APP_NAME']}.<br>
                    Jangan balas email ini.
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Attach PDF
        with open(pdf_filepath, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{pdf_filename}"'
        )
        msg.attach(part)

        # Kirim via SMTP
        server = smtplib.SMTP(config["SMTP_SERVER"], config["SMTP_PORT"])
        server.starttls()
        server.login(config["SENDER_EMAIL"], config["SENDER_PASSWORD"])
        server.send_message(msg)
        server.quit()

        return True, "Email berhasil dikirim!"

    except smtplib.SMTPAuthenticationError:
        return False, "Autentikasi SMTP gagal! Periksa App Password."
    except smtplib.SMTPException as e:
        return False, f"Error SMTP: {str(e)}"
    except FileNotFoundError:
        return False, "File PDF tidak ditemukan!"
    except Exception as e:
        return False, f"Error: {str(e)}"