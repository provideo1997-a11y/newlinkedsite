import os, secrets, csv, io, re, uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, Response, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from wtforms import StringField, EmailField, SelectField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException
import sys
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from time import perf_counter
from itsdangerous import URLSafeTimedSerializer, BadSignature
from security_utils import normalize_database_url, merge_locale_translations, csv_safe, sqlalchemy_engine_options, normalize_whatsapp_number, ensure_unique_case_reference_index
from whatsapp_utils import build_case_whatsapp_url

app = Flask(__name__, instance_relative_config=True)
# Render terminates TLS and forwards one trusted proxy hop. Never trust arbitrary client-supplied chains.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0)
os.makedirs(app.instance_path, exist_ok=True)
if os.environ.get('RENDER') and not os.environ.get('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY must be configured in Render environment variables.')
ADMIN_URL_PREFIX = os.environ.get('ADMIN_URL_PREFIX', '/private-inbox').strip()
if not ADMIN_URL_PREFIX.startswith('/') or ADMIN_URL_PREFIX.startswith('//') or '..' in ADMIN_URL_PREFIX:
    raise RuntimeError('ADMIN_URL_PREFIX must be a safe absolute URL path.')
ADMIN_URL_PREFIX = ADMIN_URL_PREFIX.rstrip('/') or '/private-inbox'

_DATABASE_URI = normalize_database_url(
    os.environ.get('DATABASE_URL'),
    'sqlite:///' + os.path.join(app.instance_path, 'yakuza.db')
)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
    SQLALCHEMY_DATABASE_URI=_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS=sqlalchemy_engine_options(_DATABASE_URI),
    SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0') == '1',
    # Flask-WTF / itsdangerous expects an integer number of seconds here.
    WTF_CSRF_TIME_LIMIT=12 * 60 * 60,
    MAX_CONTENT_LENGTH=64 * 1024,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    SESSION_REFRESH_EACH_REQUEST=True,
)
db=SQLAlchemy(app); csrf=CSRFProtect(app)
limiter=Limiter(get_remote_address, app=app, default_limits=['200 per day','50 per hour'], storage_uri=os.environ.get('RATELIMIT_STORAGE_URI','memory://'))

LANGS={
'en': {'name':'English','dir':'ltr','nav_home':'Home','nav_services':'Capabilities','nav_about':'About','nav_contact':'Contact','eyebrow':'DIGITAL TRUST • RECOVERY • COMPLIANCE','hero_a':'RECLAIM','hero_b':'YOUR DIGITAL','hero_c':'GROUND.','hero_desc':'Strategic account recovery guidance, digital risk response, and compliance consulting — built around your ownership, privacy, and control.','cta_primary':'Start a secure request','cta_secondary':'Explore capabilities','scroll':'SCROLL TO EXPLORE','status':'SYSTEMS ONLINE','trusted':'A CLEARER PATH THROUGH DIGITAL COMPLEXITY','services_title':'Precision when it matters.','services_desc':'A calm, documented process for complex digital account and trust challenges.','s1':'Account recovery guidance','s1d':'Structured, platform-approved recovery support for accounts you own or are authorized to manage.','s2':'Digital risk response','s2d':'Incident triage, evidence organization, and practical next steps after suspicious activity.','s3':'Compliance advisory','s3d':'Policy readiness, identity-verification preparation, and governance documentation.','s4':'Security posture review','s4d':'Practical account hygiene, access-control, and prevention recommendations.','process':'THE METHOD','process_title':'Clarity. Control. Closure.','p1':'Understand','p1d':'We scope the issue and confirm authorization.','p2':'Assess','p2d':'We map evidence, risks, and platform processes.','p3':'Act','p3d':'You follow a clear, documented action plan.','p4':'Strengthen','p4d':'We help reduce repeat incidents.','about_title':'Digital recovery, without shortcuts.','about_desc':'YAKUZA is a digital recovery and compliance consultancy focused on legitimate, owner-authorized support. We never ask for passwords, one-time codes, or remote access to personal accounts.','contact_title':'Let’s map your next move.','contact_desc':'Tell us what happened. Do not include passwords, verification codes, recovery keys, or sensitive identity documents.','form_name':'Your name','form_email':'Work email','form_topic':'What do you need help with?','form_message':'Briefly describe the situation','form_submit':'Send secure inquiry','topic_recovery':'Account recovery guidance','topic_risk':'Digital risk response','topic_compliance':'Compliance advisory','topic_other':'Other inquiry','footer_note':'Independent consulting. No affiliation with social platforms.','privacy':'Privacy','admin':'Team portal','sent':'Your inquiry has been received. We will review it and respond using the email you provided.','back':'Back to home','login':'Team sign in','username':'Username','password':'Password','sign_in':'Sign in','dashboard':'Inquiry dashboard','logout':'Sign out','case':'Case','status_label':'Status','new':'New','reviewing':'Reviewing','closed':'Closed','update':'Update','no_cases':'No inquiries yet.','disclaimer':'YAKUZA cannot guarantee account restoration. All recovery actions must be completed by the account owner through official platform channels.','privacy_title':'Privacy & data handling','privacy_text':'We use inquiry details only to respond to requests, maintain service records, and protect the service. Do not submit passwords, authentication codes, recovery keys, payment card data, or unnecessary sensitive documents.','loading':'INITIALIZING SECURE INTERFACE','loading_sub':'ESTABLISHING ENCRYPTED SESSION','menu':'Open menu'},
'ar': {'name':'العربية','dir':'rtl','nav_home':'الرئيسية','nav_services':'الخدمات','nav_about':'من نحن','nav_contact':'اتصل بنا','eyebrow':'الثقة الرقمية • الاستعادة • الامتثال','hero_a':'استعد','hero_b':'سيطرتك','hero_c':'الرقمية.','hero_desc':'إرشاد لاستعادة الحسابات، والاستجابة للمخاطر الرقمية، والاستشارات التنظيمية مع احترام الملكية والخصوصية.','cta_primary':'ابدأ طلباً آمناً','cta_secondary':'اكتشف خدماتنا','scroll':'اكتشف المزيد','status':'الأنظمة تعمل','trusted':'طريق أوضح وسط التعقيد الرقمي','services_title':'دقة عندما تكون مهمة.','services_desc':'منهج واضح وموثق للتحديات الرقمية المعقدة.','s1':'إرشاد استعادة الحساب','s1d':'دعم منظم ومتوافق مع المنصات للحسابات التي تملكها أو تديرها بتفويض.','s2':'الاستجابة للمخاطر الرقمية','s2d':'فرز الحوادث وتنظيم الأدلة وتحديد الخطوات بعد النشاط المشبوه.','s3':'استشارات الامتثال','s3d':'الاستعداد للسياسات والتحقق من الهوية وتوثيق الحوكمة.','s4':'مراجعة الوضع الأمني','s4d':'توصيات عملية للنظافة الرقمية وإدارة الوصول والوقاية.','process':'المنهجية','process_title':'وضوح. تحكم. إغلاق.','p1':'الفهم','p1d':'نحدد المشكلة ونتحقق من التفويض.','p2':'التقييم','p2d':'نراجع الأدلة والمخاطر وإجراءات المنصة.','p3':'التنفيذ','p3d':'تتبع خطة عمل واضحة وموثقة.','p4':'التعزيز','p4d':'نساعد على تقليل تكرار الحوادث.','about_title':'استعادة رقمية بلا اختصارات.','about_desc':'ياكوزا استشارات للاستعادة الرقمية والامتثال، وتركز على الدعم المشروع والمصرح به من المالك. لا نطلب كلمات المرور أو رموز التحقق أو الوصول عن بُعد.','contact_title':'لنحدد خطوتك التالية.','contact_desc':'اشرح ما حدث. لا ترسل كلمات مرور أو رموز تحقق أو مفاتيح استعادة أو وثائق هوية حساسة.','form_name':'الاسم','form_email':'البريد الإلكتروني','form_topic':'نوع المساعدة','form_message':'وصف مختصر للحالة','form_submit':'إرسال طلب آمن','topic_recovery':'إرشاد استعادة الحساب','topic_risk':'الاستجابة للمخاطر الرقمية','topic_compliance':'استشارات الامتثال','topic_other':'استفسار آخر','footer_note':'استشارات مستقلة وغير تابعة لمنصات التواصل.','privacy':'الخصوصية','admin':'بوابة الفريق','sent':'تم استلام طلبك. سنراجعه ونتواصل معك عبر البريد المقدم.','back':'العودة للرئيسية','login':'دخول الفريق','username':'اسم المستخدم','password':'كلمة المرور','sign_in':'دخول','dashboard':'لوحة الطلبات','logout':'خروج','case':'الطلب','status_label':'الحالة','new':'جديد','reviewing':'قيد المراجعة','closed':'مغلق','update':'تحديث','no_cases':'لا توجد طلبات بعد.','disclaimer':'لا تضمن ياكوزا استعادة الحساب. يجب على المالك تنفيذ جميع الإجراءات عبر القنوات الرسمية للمنصة.','privacy_title':'الخصوصية ومعالجة البيانات','privacy_text':'نستخدم بيانات الطلب للرد على الاستفسارات وإدارة السجلات وحماية الخدمة. لا ترسل كلمات مرور أو رموز مصادقة أو مفاتيح استعادة أو بيانات بطاقات الدفع.','loading':'تهيئة الواجهة الآمنة','loading_sub':'إنشاء جلسة مشفرة','menu':'فتح القائمة'},
'fr': {'name':'Français','dir':'ltr','nav_home':'Accueil','nav_services':'Expertises','nav_about':'À propos','nav_contact':'Contact','eyebrow':'CONFIANCE NUMÉRIQUE • RÉCUPÉRATION • CONFORMITÉ','hero_a':'REPRENEZ','hero_b':'LE CONTRÔLE','hero_c':'NUMÉRIQUE.','hero_desc':'Conseil en récupération de comptes, réponse aux risques numériques et conformité, dans le respect de votre propriété et de votre confidentialité.','cta_primary':'Créer une demande sécurisée','cta_secondary':'Découvrir nos expertises','scroll':'DÉFILER POUR EXPLORER','status':'SYSTÈMES EN LIGNE','trusted':'UN PARCOURS PLUS CLAIR DANS LA COMPLEXITÉ NUMÉRIQUE','services_title':'La précision au bon moment.','services_desc':'Un processus clair et documenté pour les défis numériques complexes.','s1':'Conseil en récupération','s1d':'Accompagnement conforme aux plateformes pour les comptes qui vous appartiennent ou que vous gérez avec autorisation.','s2':'Réponse aux risques numériques','s2d':'Tri des incidents, organisation des preuves et prochaines étapes après une activité suspecte.','s3':'Conseil en conformité','s3d':'Préparation aux politiques, vérification d’identité et documentation de gouvernance.','s4':'Évaluation de sécurité','s4d':'Bonnes pratiques de compte, contrôle des accès et prévention.','process':'LA MÉTHODE','process_title':'Clarté. Contrôle. Résolution.','p1':'Comprendre','p1d':'Cadrer le problème et confirmer l’autorisation.','p2':'Évaluer','p2d':'Cartographier les preuves, risques et procédures.','p3':'Agir','p3d':'Suivre un plan d’action documenté.','p4':'Renforcer','p4d':'Réduire le risque de récidive.','about_title':'La récupération numérique, sans raccourcis.','about_desc':'YAKUZA est un cabinet de conseil indépendant axé sur l’assistance légitime et autorisée par le propriétaire. Nous ne demandons jamais de mots de passe, codes à usage unique ou accès à distance.','contact_title':'Définissons la prochaine étape.','contact_desc':'Expliquez la situation. N’incluez aucun mot de passe, code, clé de récupération ou document d’identité sensible.','form_name':'Votre nom','form_email':'E-mail professionnel','form_topic':'Votre besoin','form_message':'Décrivez brièvement la situation','form_submit':'Envoyer la demande','topic_recovery':'Conseil en récupération','topic_risk':'Réponse aux risques numériques','topic_compliance':'Conseil en conformité','topic_other':'Autre demande','footer_note':'Conseil indépendant, sans affiliation aux plateformes.','privacy':'Confidentialité','admin':'Espace équipe','sent':'Votre demande a bien été reçue.','back':'Retour à l’accueil','login':'Connexion équipe','username':'Identifiant','password':'Mot de passe','sign_in':'Se connecter','dashboard':'Tableau des demandes','logout':'Déconnexion','case':'Dossier','status_label':'Statut','new':'Nouveau','reviewing':'En cours','closed':'Clos','update':'Mettre à jour','no_cases':'Aucune demande.','disclaimer':'YAKUZA ne garantit pas la restauration d’un compte. Le propriétaire doit utiliser les canaux officiels.','privacy_title':'Confidentialité et données','privacy_text':'Les informations servent à répondre aux demandes et à protéger le service. Ne transmettez aucun mot de passe, code, clé de récupération ou donnée bancaire.','loading':'INITIALISATION DE L’INTERFACE SÉCURISÉE','loading_sub':'ÉTABLISSEMENT DE LA SESSION','menu':'Ouvrir le menu'},
'es': {'name':'Español','dir':'ltr','nav_home':'Inicio','nav_services':'Servicios','nav_about':'Nosotros','nav_contact':'Contacto','eyebrow':'CONFIANZA DIGITAL • RECUPERACIÓN • CUMPLIMIENTO','hero_a':'RECUPERA','hero_b':'TU CONTROL','hero_c':'DIGITAL.','hero_desc':'Orientación para recuperar cuentas, responder a riesgos digitales y asesoría de cumplimiento, respetando tu propiedad y privacidad.','cta_primary':'Iniciar solicitud segura','cta_secondary':'Ver servicios','scroll':'DESPLAZA PARA EXPLORAR','status':'SISTEMAS ACTIVOS','trusted':'UN CAMINO MÁS CLARO EN LA COMPLEJIDAD DIGITAL','services_title':'Precisión cuando importa.','services_desc':'Un proceso claro y documentado para retos digitales complejos.','s1':'Orientación para recuperar cuentas','s1d':'Apoyo conforme a las plataformas para cuentas propias o gestionadas con autorización.','s2':'Respuesta a riesgos digitales','s2d':'Clasificación de incidentes, organización de pruebas y próximos pasos ante actividad sospechosa.','s3':'Asesoría de cumplimiento','s3d':'Preparación de políticas, verificación de identidad y documentación de gobernanza.','s4':'Revisión de seguridad','s4d':'Higiene de cuentas, control de acceso y prevención.','process':'EL MÉTODO','process_title':'Claridad. Control. Cierre.','p1':'Comprender','p1d':'Definimos el problema y confirmamos autorización.','p2':'Evaluar','p2d':'Revisamos pruebas, riesgos y procesos oficiales.','p3':'Actuar','p3d':'Sigues un plan claro y documentado.','p4':'Reforzar','p4d':'Reducimos la posibilidad de recurrencia.','about_title':'Recuperación digital sin atajos.','about_desc':'YAKUZA ofrece consultoría independiente y asistencia legítima autorizada por el propietario. Nunca pedimos contraseñas, códigos de un solo uso ni acceso remoto.','contact_title':'Definamos el siguiente paso.','contact_desc':'Cuéntanos qué ocurrió. No incluyas contraseñas, códigos, claves de recuperación ni documentos sensibles.','form_name':'Tu nombre','form_email':'Correo electrónico','form_topic':'¿Qué necesitas?','form_message':'Describe brevemente la situación','form_submit':'Enviar consulta segura','topic_recovery':'Orientación de recuperación','topic_risk':'Respuesta a riesgos digitales','topic_compliance':'Asesoría de cumplimiento','topic_other':'Otra consulta','footer_note':'Consultoría independiente, sin afiliación a plataformas.','privacy':'Privacidad','admin':'Portal del equipo','sent':'Hemos recibido tu consulta.','back':'Volver al inicio','login':'Acceso del equipo','username':'Usuario','password':'Contraseña','sign_in':'Entrar','dashboard':'Panel de consultas','logout':'Salir','case':'Caso','status_label':'Estado','new':'Nuevo','reviewing':'En revisión','closed':'Cerrado','update':'Actualizar','no_cases':'Aún no hay consultas.','disclaimer':'YAKUZA no garantiza la restauración de cuentas. El titular debe usar los canales oficiales.','privacy_title':'Privacidad y datos','privacy_text':'Usamos los datos para responder y proteger el servicio. No envíes contraseñas, códigos, claves de recuperación ni datos bancarios.','loading':'INICIANDO INTERFAZ SEGURA','loading_sub':'ESTABLECIENDO SESIÓN','menu':'Abrir menú'},
'de': {'name':'Deutsch','dir':'ltr','nav_home':'Start','nav_services':'Leistungen','nav_about':'Über uns','nav_contact':'Kontakt','eyebrow':'DIGITALES VERTRAUEN • WIEDERHERSTELLUNG • COMPLIANCE','hero_a':'HOLEN SIE','hero_b':'DIE KONTROLLE','hero_c':'ZURÜCK.','hero_desc':'Beratung zur Kontowiederherstellung, Reaktion auf digitale Risiken und Compliance — mit Fokus auf Eigentum und Datenschutz.','cta_primary':'Sichere Anfrage starten','cta_secondary':'Leistungen entdecken','scroll':'WEITER ENTDECKEN','status':'SYSTEME ONLINE','trusted':'KLARHEIT IN DIGITALER KOMPLEXITÄT','services_title':'Präzision, wenn es darauf ankommt.','services_desc':'Ein klarer, dokumentierter Prozess für komplexe digitale Herausforderungen.','s1':'Beratung zur Kontowiederherstellung','s1d':'Plattformkonforme Unterstützung für eigene oder autorisiert verwaltete Konten.','s2':'Reaktion auf digitale Risiken','s2d':'Vorfallbewertung, Beweissicherung und nächste Schritte bei verdächtigen Aktivitäten.','s3':'Compliance-Beratung','s3d':'Richtlinien, Identitätsprüfung und Governance-Dokumentation.','s4':'Sicherheitsprüfung','s4d':'Kontohygiene, Zugriffskontrolle und Prävention.','process':'DER ANSATZ','process_title':'Klarheit. Kontrolle. Abschluss.','p1':'Verstehen','p1d':'Problem eingrenzen und Berechtigung bestätigen.','p2':'Bewerten','p2d':'Belege, Risiken und Plattformprozesse prüfen.','p3':'Handeln','p3d':'Einem klaren Maßnahmenplan folgen.','p4':'Stärken','p4d':'Wiederholungsrisiken reduzieren.','about_title':'Digitale Wiederherstellung ohne Abkürzungen.','about_desc':'YAKUZA ist eine unabhängige Beratung für legitime, vom Eigentümer autorisierte Unterstützung. Wir fragen niemals nach Passwörtern, Einmalcodes oder Fernzugriff.','contact_title':'Planen wir den nächsten Schritt.','contact_desc':'Beschreiben Sie den Vorfall. Keine Passwörter, Codes, Wiederherstellungsschlüssel oder sensiblen Ausweisdokumente senden.','form_name':'Ihr Name','form_email':'E-Mail','form_topic':'Wobei benötigen Sie Hilfe?','form_message':'Situation kurz beschreiben','form_submit':'Sichere Anfrage senden','topic_recovery':'Kontowiederherstellung','topic_risk':'Digitale Risikoreaktion','topic_compliance':'Compliance-Beratung','topic_other':'Sonstige Anfrage','footer_note':'Unabhängige Beratung, keine Plattformzugehörigkeit.','privacy':'Datenschutz','admin':'Teamportal','sent':'Ihre Anfrage ist eingegangen.','back':'Zur Startseite','login':'Team-Anmeldung','username':'Benutzername','password':'Passwort','sign_in':'Anmelden','dashboard':'Anfragenübersicht','logout':'Abmelden','case':'Anfrage','status_label':'Status','new':'Neu','reviewing':'In Prüfung','closed':'Geschlossen','update':'Aktualisieren','no_cases':'Noch keine Anfragen.','disclaimer':'YAKUZA garantiert keine Kontowiederherstellung. Eigentümer müssen offizielle Plattformkanäle nutzen.','privacy_title':'Datenschutz und Daten','privacy_text':'Angaben werden zur Beantwortung und zum Schutz des Dienstes verwendet. Keine Passwörter, Codes, Wiederherstellungsschlüssel oder Zahlungsdaten senden.','loading':'SICHERE OBERFLÄCHE WIRD GESTARTET','loading_sub':'SITZUNG WIRD AUFGEBAUT','menu':'Menü öffnen'},
'it': {'name':'Italiano','dir':'ltr','nav_home':'Home','nav_services':'Servizi','nav_about':'Chi siamo','nav_contact':'Contatti','eyebrow':'FIDUCIA DIGITALE • RECUPERO • CONFORMITÀ','hero_a':'RIPRENDI','hero_b':'IL TUO CONTROLLO','hero_c':'DIGITALE.','hero_desc':'Consulenza per il recupero account, risposta ai rischi digitali e conformità, nel rispetto della proprietà e della privacy.','cta_primary':'Avvia una richiesta sicura','cta_secondary':'Scopri i servizi','scroll':'SCORRI PER ESPLORARE','status':'SISTEMI ONLINE','trusted':'PIÙ CHIAREZZA NELLA COMPLESSITÀ DIGITALE','services_title':'Precisione quando serve.','services_desc':'Un processo chiaro e documentato per sfide digitali complesse.','s1':'Consulenza recupero account','s1d':'Supporto conforme alle piattaforme per account di tua proprietà o gestiti con autorizzazione.','s2':'Risposta ai rischi digitali','s2d':'Valutazione incidenti, organizzazione prove e passaggi successivi dopo attività sospette.','s3':'Consulenza conformità','s3d':'Preparazione alle policy, verifica identità e documentazione governance.','s4':'Revisione sicurezza','s4d':'Igiene degli account, controllo accessi e prevenzione.','process':'IL METODO','process_title':'Chiarezza. Controllo. Soluzione.','p1':'Comprendere','p1d':'Definire il problema e confermare l’autorizzazione.','p2':'Valutare','p2d':'Mappare prove, rischi e procedure della piattaforma.','p3':'Agire','p3d':'Seguire un piano d’azione documentato.','p4':'Rafforzare','p4d':'Ridurre il rischio di nuovi incidenti.','about_title':'Recupero digitale senza scorciatoie.','about_desc':'YAKUZA è una consulenza indipendente per supporto legittimo e autorizzato dal proprietario. Non chiediamo mai password, codici temporanei o accesso remoto.','contact_title':'Definiamo il prossimo passo.','contact_desc':'Descrivi cosa è successo. Non includere password, codici, chiavi di recupero o documenti sensibili.','form_name':'Nome','form_email':'Email','form_topic':'Di cosa hai bisogno?','form_message':'Descrivi brevemente la situazione','form_submit':'Invia richiesta sicura','topic_recovery':'Consulenza recupero account','topic_risk':'Risposta ai rischi digitali','topic_compliance':'Consulenza conformità','topic_other':'Altra richiesta','footer_note':'Consulenza indipendente, non affiliata alle piattaforme.','privacy':'Privacy','admin':'Portale team','sent':'La richiesta è stata ricevuta.','back':'Torna alla home','login':'Accesso team','username':'Nome utente','password':'Password','sign_in':'Accedi','dashboard':'Dashboard richieste','logout':'Esci','case':'Caso','status_label':'Stato','new':'Nuovo','reviewing':'In revisione','closed':'Chiuso','update':'Aggiorna','no_cases':'Nessuna richiesta.','disclaimer':'YAKUZA non garantisce il ripristino degli account. Il proprietario deve usare i canali ufficiali.','privacy_title':'Privacy e dati','privacy_text':'Usiamo i dati per rispondere e proteggere il servizio. Non inviare password, codici, chiavi di recupero o dati di pagamento.','loading':'AVVIO INTERFACCIA SICURA','loading_sub':'CREAZIONE SESSIONE','menu':'Apri menu'}
}


# Additional localized interfaces. English remains the fallback for non-translated legal text.
LANGS.update({
'pt': {'name':'Português','dir':'ltr','nav_home':'Início','nav_services':'Serviços','nav_about':'Sobre','nav_contact':'Contato','eyebrow':'CONFIANÇA DIGITAL • RECUPERAÇÃO • CONFORMIDADE','hero_a':'REASSUMA','hero_b':'O CONTROLE','hero_c':'DIGITAL.','hero_desc':'Orientação para recuperação de contas, resposta a riscos digitais e consultoria de conformidade, respeitando sua propriedade e privacidade.','cta_primary':'Iniciar solicitação segura','cta_secondary':'Explorar serviços','scroll':'ROLE PARA EXPLORAR','status':'SISTEMAS ONLINE','trusted':'UM CAMINHO MAIS CLARO NA COMPLEXIDADE DIGITAL','services_title':'Precisão quando importa.','services_desc':'Um processo claro e documentado para desafios digitais complexos.','s1':'Orientação para recuperação de contas','s1d':'Suporte alinhado às plataformas para contas próprias ou geridas com autorização.','s2':'Resposta a riscos digitais','s2d':'Triagem de incidentes, organização de evidências e próximos passos após atividade suspeita.','s3':'Consultoria de conformidade','s3d':'Preparação para políticas, verificação de identidade e documentação de governança.','s4':'Revisão de segurança','s4d':'Boas práticas de conta, controle de acesso e prevenção.','process':'O MÉTODO','process_title':'Clareza. Controle. Resolução.','p1':'Entender','p1d':'Definir o problema e confirmar autorização.','p2':'Avaliar','p2d':'Mapear evidências, riscos e processos da plataforma.','p3':'Agir','p3d':'Seguir um plano de ação documentado.','p4':'Fortalecer','p4d':'Reduzir o risco de recorrência.','about_title':'Recuperação digital sem atalhos.','about_desc':'A YAKUZA é uma consultoria independente focada em suporte legítimo e autorizado pelo titular. Nunca solicitamos senhas, códigos temporários ou acesso remoto.','contact_title':'Vamos definir o próximo passo.','contact_desc':'Conte o que aconteceu. Não inclua senhas, códigos, chaves de recuperação ou documentos sensíveis.','form_name':'Seu nome','form_email':'E-mail','form_topic':'Como podemos ajudar?','form_message':'Descreva brevemente a situação','form_submit':'Enviar solicitação segura','topic_recovery':'Orientação para recuperação','topic_risk':'Resposta a riscos digitais','topic_compliance':'Consultoria de conformidade','topic_other':'Outra solicitação','footer_note':'Consultoria independente, sem vínculo com plataformas.','privacy':'Privacidade','admin':'Portal da equipe','sent':'Sua solicitação foi recebida.','back':'Voltar ao início','login':'Acesso da equipe','username':'Usuário','password':'Senha','sign_in':'Entrar','dashboard':'Painel de solicitações','logout':'Sair','case':'Caso','status_label':'Status','new':'Novo','reviewing':'Em análise','closed':'Fechado','update':'Atualizar','no_cases':'Ainda não há solicitações.','disclaimer':'A YAKUZA não garante a restauração de contas. O titular deve usar os canais oficiais da plataforma.','privacy_title':'Privacidade e dados','privacy_text':'Usamos os dados para responder às solicitações e proteger o serviço. Não envie senhas, códigos, chaves de recuperação ou dados bancários.','loading':'INICIALIZANDO INTERFACE SEGURA','loading_sub':'ESTABELECENDO SESSÃO','menu':'Abrir menu'},
'tr': {'name':'Türkçe','dir':'ltr','nav_home':'Ana Sayfa','nav_services':'Hizmetler','nav_about':'Hakkımızda','nav_contact':'İletişim','eyebrow':'DİJİTAL GÜVEN • KURTARMA • UYUM','hero_a':'DİJİTAL','hero_b':'KONTROLÜNÜ','hero_c':'GERİ AL.','hero_desc':'Hesap kurtarma rehberliği, dijital risk müdahalesi ve uyum danışmanlığı; mülkiyetinize ve gizliliğinize saygıyla.','cta_primary':'Güvenli talep başlat','cta_secondary':'Hizmetleri keşfet','scroll':'KEŞFETMEK İÇİN KAYDIR','status':'SİSTEMLER ÇEVRİMİÇİ','trusted':'DİJİTAL KARMAŞADA DAHA NET BİR YOL','services_title':'Önemli anlarda hassasiyet.','services_desc':'Karmaşık dijital sorunlar için açık ve belgeli süreç.','s1':'Hesap kurtarma rehberliği','s1d':'Sahibi olduğunuz veya yetkiyle yönettiğiniz hesaplar için platform kurallarına uygun destek.','s2':'Dijital risk müdahalesi','s2d':'Şüpheli etkinlik sonrası olay değerlendirmesi, kanıt düzenleme ve sonraki adımlar.','s3':'Uyum danışmanlığı','s3d':'Politika hazırlığı, kimlik doğrulama ve yönetişim belgeleri.','s4':'Güvenlik değerlendirmesi','s4d':'Hesap güvenliği, erişim kontrolü ve önleme önerileri.','process':'YÖNTEM','process_title':'Netlik. Kontrol. Çözüm.','p1':'Anla','p1d':'Sorunu tanımla ve yetkiyi doğrula.','p2':'Değerlendir','p2d':'Kanıtları, riskleri ve platform süreçlerini incele.','p3':'Harekete geç','p3d':'Belgelenmiş bir eylem planını izle.','p4':'Güçlendir','p4d':'Tekrarlama riskini azalt.','about_title':'Kestirme yol olmadan dijital kurtarma.','about_desc':'YAKUZA, hesap sahibinin yetkilendirdiği meşru desteğe odaklanan bağımsız bir danışmanlıktır. Şifre, tek kullanımlık kod veya uzaktan erişim istemeyiz.','contact_title':'Sonraki adımı birlikte belirleyelim.','contact_desc':'Ne olduğunu anlatın. Şifre, doğrulama kodu, kurtarma anahtarı veya hassas belge göndermeyin.','form_name':'Adınız','form_email':'E-posta','form_topic':'Hangi konuda yardım?','form_message':'Durumu kısaca açıklayın','form_submit':'Güvenli talep gönder','topic_recovery':'Hesap kurtarma rehberliği','topic_risk':'Dijital risk müdahalesi','topic_compliance':'Uyum danışmanlığı','topic_other':'Diğer talep','footer_note':'Bağımsız danışmanlık; platformlarla bağlantısı yoktur.','privacy':'Gizlilik','admin':'Ekip portalı','sent':'Talebiniz alındı.','back':'Ana sayfaya dön','login':'Ekip girişi','username':'Kullanıcı adı','password':'Şifre','sign_in':'Giriş yap','dashboard':'Talep paneli','logout':'Çıkış','case':'Dosya','status_label':'Durum','new':'Yeni','reviewing':'İnceleniyor','closed':'Kapalı','update':'Güncelle','no_cases':'Henüz talep yok.','disclaimer':'YAKUZA hesap kurtarmayı garanti etmez. Tüm işlemler hesap sahibi tarafından resmî platform kanallarından yapılmalıdır.','privacy_title':'Gizlilik ve veri','privacy_text':'Bilgileri talepleri yanıtlamak ve hizmeti korumak için kullanırız. Şifre, kod, kurtarma anahtarı veya ödeme bilgisi göndermeyin.','loading':'GÜVENLİ ARAYÜZ BAŞLATILIYOR','loading_sub':'OTURUM OLUŞTURULUYOR','menu':'Menüyü aç'},
'zh': {'name':'简体中文','dir':'ltr','nav_home':'首页','nav_services':'服务','nav_about':'关于我们','nav_contact':'联系','eyebrow':'数字信任 • 账户恢复 • 合规','hero_a':'重新掌握','hero_b':'数字世界','hero_c':'主动权。','hero_desc':'提供账户恢复指导、数字风险响应和合规咨询，尊重您的账户所有权与隐私。','cta_primary':'提交安全请求','cta_secondary':'探索服务','scroll':'向下探索','status':'系统在线','trusted':'让复杂数字问题更清晰','services_title':'关键时刻，精准应对。','services_desc':'以清晰、可记录的流程处理复杂数字挑战。','s1':'账户恢复指导','s1d':'针对您拥有或获授权管理的账户，提供符合平台规则的支持。','s2':'数字风险响应','s2d':'可疑活动后的事件分级、证据整理与后续建议。','s3':'合规咨询','s3d':'平台政策准备、身份验证准备和治理文档。','s4':'安全状况评估','s4d':'账户安全、访问控制和预防建议。','process':'工作方法','process_title':'清晰。掌控。解决。','p1':'了解','p1d':'明确问题并确认授权。','p2':'评估','p2d':'梳理证据、风险和平台流程。','p3':'行动','p3d':'遵循清晰且有记录的行动计划。','p4':'强化','p4d':'降低问题再次发生的风险。','about_title':'数字恢复，不走捷径。','about_desc':'YAKUZA 是独立的数字恢复与合规咨询机构，只提供合法且经账户所有者授权的支持。我们绝不会索要密码、一次性验证码或远程访问权限。','contact_title':'一起规划下一步。','contact_desc':'请描述发生的情况。请勿提供密码、验证码、恢复密钥或敏感身份证件。','form_name':'姓名','form_email':'电子邮箱','form_topic':'需要哪类帮助？','form_message':'简要描述情况','form_submit':'发送安全请求','topic_recovery':'账户恢复指导','topic_risk':'数字风险响应','topic_compliance':'合规咨询','topic_other':'其他咨询','footer_note':'独立咨询机构，与社交平台无关联。','privacy':'隐私','admin':'团队入口','sent':'已收到您的请求。','back':'返回首页','login':'团队登录','username':'用户名','password':'密码','sign_in':'登录','dashboard':'请求管理','logout':'退出','case':'请求','status_label':'状态','new':'新建','reviewing':'审核中','closed':'已关闭','update':'更新','no_cases':'暂无请求。','disclaimer':'YAKUZA 不保证账户恢复。所有恢复操作必须由账户所有者通过平台官方渠道完成。','privacy_title':'隐私与数据处理','privacy_text':'我们仅使用请求信息来回复咨询并维护服务安全。请勿提交密码、验证码、恢复密钥或银行卡信息。','loading':'正在初始化安全界面','loading_sub':'正在建立会话','menu':'打开菜单'},
'ja': {'name':'日本語','dir':'ltr','nav_home':'ホーム','nav_services':'サービス','nav_about':'私たちについて','nav_contact':'お問い合わせ','eyebrow':'デジタル信頼 • 復旧支援 • コンプライアンス','hero_a':'デジタルの','hero_b':'主導権を','hero_c':'取り戻す。','hero_desc':'アカウント復旧のガイダンス、デジタルリスク対応、コンプライアンス相談を、所有権とプライバシーを尊重して提供します。','cta_primary':'安全な相談を開始','cta_secondary':'サービスを見る','scroll':'スクロールして探索','status':'システム稼働中','trusted':'複雑なデジタル課題を、より明確に','services_title':'重要な場面で、的確に。','services_desc':'複雑なデジタル課題に対する明確で記録可能なプロセス。','s1':'アカウント復旧ガイダンス','s1d':'本人所有または正当な権限のあるアカウントに対する、プラットフォーム規約に沿った支援。','s2':'デジタルリスク対応','s2d':'不審な活動後のインシデント評価、証拠整理、次の対応策。','s3':'コンプライアンス相談','s3d':'ポリシー対応、本人確認の準備、ガバナンス文書。','s4':'セキュリティ評価','s4d':'アカウント衛生、アクセス管理、予防策の提案。','process':'進め方','process_title':'明確に。確実に。解決へ。','p1':'把握','p1d':'課題を整理し、権限を確認します。','p2':'評価','p2d':'証拠、リスク、プラットフォームの手順を確認します。','p3':'実行','p3d':'明確で記録された計画に沿って進めます。','p4':'強化','p4d':'再発リスクの低減を支援します。','about_title':'近道に頼らないデジタル復旧。','about_desc':'YAKUZA は、所有者の許可に基づく正当な支援を行う独立系コンサルティングです。パスワード、ワンタイムコード、遠隔アクセスを求めることはありません。','contact_title':'次の一歩を一緒に考えましょう。','contact_desc':'状況をお知らせください。パスワード、認証コード、復旧キー、機密性の高い本人確認書類は送信しないでください。','form_name':'お名前','form_email':'メールアドレス','form_topic':'ご相談内容','form_message':'状況を簡潔にご記入ください','form_submit':'安全な問い合わせを送信','topic_recovery':'アカウント復旧ガイダンス','topic_risk':'デジタルリスク対応','topic_compliance':'コンプライアンス相談','topic_other':'その他のお問い合わせ','footer_note':'独立したコンサルティングであり、各プラットフォームとは無関係です。','privacy':'プライバシー','admin':'チームポータル','sent':'お問い合わせを受け付けました。','back':'ホームに戻る','login':'チームログイン','username':'ユーザー名','password':'パスワード','sign_in':'ログイン','dashboard':'問い合わせ管理','logout':'ログアウト','case':'案件','status_label':'ステータス','new':'新規','reviewing':'確認中','closed':'完了','update':'更新','no_cases':'問い合わせはまだありません。','disclaimer':'YAKUZA はアカウント復旧を保証しません。すべての復旧操作は所有者が公式窓口を通じて行う必要があります。','privacy_title':'プライバシーとデータ','privacy_text':'お問い合わせへの対応とサービス保護のために情報を使用します。パスワード、認証コード、復旧キー、決済情報は送信しないでください。','loading':'セキュア画面を初期化中','loading_sub':'セッションを確立中','menu':'メニューを開く'}
})

LANGS['ar-tn']={**LANGS['ar'], 'name':'تونسي / العربية', 'nav_home':'الرئيسية', 'nav_services':'شنوة نقدّمو', 'nav_about':'علينا', 'nav_contact':'اتصل بينا', 'contact_title':'احكيلنا شنوة صار', 'contact_desc':'عمّر الطلب بالتفاصيل الضرورية، وما تبعثش كلمة السر ولا كود التثبّت.', 'form_name':'اسمك', 'form_email':'الإيميل متاعك', 'form_topic':'نوع المشكلة', 'form_message':'فسّرنا باختصار شنوة صار', 'form_submit':'ابعث الطلب بأمان', 'sent':'وصلنا طلبك، ونعطيوه رقم متابعة.', 'dashboard':'طلبات الحرفاء', 'no_cases':'ما فما حتى طلب توّة.', 'login':'دخول الفريق', 'username':'اسم المستخدم', 'password':'كلمة السر', 'sign_in':'ادخل', 'logout':'اخرج', 'privacy':'الخصوصية'}

# Translatable case-intake labels. Untranslated supported languages fall back to English.
FORM_COPY = {
'en': {'case_kicker':'SECURE CASE INTAKE','case_title':'Tell us what happened.','case_intro':'A few details help us route your request. Usually takes 2–3 minutes.','step_identity':'YOUR DETAILS','step_incident':'ABOUT THE ISSUE','step_next':'NEXT STEP','full_name':'Full name','email_address':'Email address','platform_label':'Platform','platform_none':'Not specified','platform_instagram':'Instagram','platform_facebook':'Facebook','platform_tiktok':'TikTok','platform_google':'Google','platform_x':'X','platform_linkedin':'LinkedIn','platform_other':'Other','handle_label':'Account handle or profile link','optional':'Optional','handle_hint':'@username or public profile URL','phone_label':'Phone / WhatsApp','phone_hint':'Include country code, e.g. +216…','date_label':'Incident date','date_hint':'An approximate date is fine','category_label':'What do you need?','cat_recovery':'Account access & recovery','cat_hacked':'Hacked account response','cat_impersonation':'Impersonation & fake profiles','cat_scam':'Scam / fraud incident review','cat_privacy':'Privacy & data exposure','cat_reputation':'Brand & reputation protection','cat_compliance':'Policy & compliance guidance','cat_security':'Security check-up & prevention','cat_other':'Something else','priority_label':'How urgent is it?','priority_normal':'Normal','priority_high':'High','priority_critical':'Critical — active incident','evidence_label':'Evidence link','evidence_hint':'HTTPS link only. Never share passwords or private codes.','story_label':'Describe what happened','story_hint':'What happened, when it started, what you tried and any platform response. Minimum 25 characters.','story_count':'characters','preferred_label':'How would you like to continue?','private_title':'Private inbox review','private_desc':'Save your case for review in the protected dashboard.','whatsapp_title':'Continue on WhatsApp','whatsapp_desc':'Your case is saved first. After saving, click the WhatsApp button on the receipt to open a prepared message you can review and send.','human_label':'Human check','human_hint':'Enter the answer','consent_text':'I own this account or have permission to request help, and the information is accurate to the best of my knowledge.','privacy_note':'We use these details only to assess and respond. Never send passwords, one-time codes, recovery keys, payment details or unnecessary identity documents. Automated risk flags are review prompts, not a fraud finding.','submit_case':'Create secure case','secure_note':'Secure intake · Your case reference appears after submission','services_heading':'More ways we can help','services_intro':'Choose the closest service. We review the facts before recommending next steps.','service_1':'Account access & recovery planning','service_1d':'Official-channel recovery guidance, ownership documentation and next-step planning.','service_2':'Compromised account response','service_2d':'Containment checklist, session and access review, evidence timeline and recovery preparation.','service_3':'Impersonation & fake profile reporting','service_3d':'Evidence capture, platform report preparation and follow-up tracking.','service_4':'Scam incident assessment','service_4d':'Incident timeline, scam warning signs and evidence organization. No guarantee of fund recovery.','service_5':'Privacy & data exposure response','service_5d':'Exposure triage, account-safety steps and practical notification guidance.','service_6':'Brand & reputation protection','service_6d':'Public-profile monitoring plan, impersonation response and reputation-risk recommendations.','service_7':'Policy & compliance advisory','service_7d':'Platform policy review, documentation readiness and compliance process guidance.','service_8':'Security check-up & prevention','service_8d':'Account-hardening checklist, MFA guidance and safer access practices.'},
'fr': {'case_kicker':'OUVERTURE DE DOSSIER SÉCURISÉE','case_title':'Expliquez-nous ce qui s’est passé.','case_intro':'Quelques détails nous aident à orienter votre demande. Environ 2 à 3 minutes.','step_identity':'VOS COORDONNÉES','step_incident':'LE PROBLÈME','step_next':'SUITE','full_name':'Nom complet','email_address':'Adresse e-mail','platform_label':'Plateforme','platform_none':'Non précisée','handle_label':'Identifiant ou lien du profil','optional':'Facultatif','handle_hint':'@identifiant ou URL publique','phone_label':'Téléphone / WhatsApp','phone_hint':'Avec indicatif pays, ex. +216…','date_label':'Date de l’incident','date_hint':'Une date approximative suffit','category_label':'De quel service avez-vous besoin ?','cat_recovery':'Accès et récupération de compte','cat_hacked':'Réponse à un compte piraté','cat_impersonation':'Usurpation et faux profils','cat_scam':'Analyse d’une arnaque ou fraude','cat_privacy':'Confidentialité et fuite de données','cat_reputation':'Protection de marque et réputation','cat_compliance':'Conseil en règles et conformité','cat_security':'Audit de sécurité et prévention','cat_other':'Autre demande','priority_label':'Niveau d’urgence','priority_normal':'Normal','priority_high':'Élevé','priority_critical':'Critique — incident en cours','evidence_label':'Lien vers les preuves','evidence_hint':'Lien HTTPS uniquement. Aucun mot de passe ni code privé.','story_label':'Décrivez le problème','story_hint':'Que s’est-il passé, quand, quelles démarches avez-vous tentées et quelle réponse avez-vous reçue ? 25 caractères minimum.','story_count':'caractères','preferred_label':'Comment souhaitez-vous poursuivre ?','private_title':'Examen dans la boîte privée','private_desc':'Votre dossier est enregistré pour examen dans le tableau de bord.','whatsapp_title':'Continuer sur WhatsApp','whatsapp_desc':'Votre dossier est d’abord enregistré. Sur le reçu, cliquez sur le bouton WhatsApp pour ouvrir un message prérempli, le vérifier et l’envoyer vous-même.','human_label':'Vérification humaine','human_hint':'Votre réponse','consent_text':'Je suis propriétaire du compte ou autorisé à demander de l’aide, et les informations sont exactes à ma connaissance.','privacy_note':'Ces informations servent uniquement à traiter votre demande. N’envoyez jamais de mot de passe, code temporaire, clé de récupération, donnée bancaire ou document inutile. Les alertes automatisées ne prouvent pas une fraude.','submit_case':'Créer mon dossier','secure_note':'Formulaire sécurisé · Référence communiquée après envoi','services_heading':'Autres services disponibles','services_intro':'Choisissez le service le plus proche. Les faits sont examinés avant toute recommandation.'},
'ar': {'case_kicker':'فتح ملف آمن','case_title':'أخبرنا بما حدث.','case_intro':'بعض التفاصيل تساعدنا على توجيه طلبك. يستغرق نحو دقيقتين أو ثلاث.','step_identity':'بياناتك','step_incident':'تفاصيل المشكلة','step_next':'الخطوة التالية','full_name':'الاسم الكامل','email_address':'البريد الإلكتروني','platform_label':'المنصة','platform_none':'غير محدد','handle_label':'اسم الحساب أو رابط الملف','optional':'اختياري','handle_hint':'@اسم المستخدم أو رابط عام','phone_label':'الهاتف / واتساب','phone_hint':'مع رمز الدولة، مثل +216…','date_label':'تاريخ الحادثة','date_hint':'يمكن إدخال تاريخ تقريبي','category_label':'ما الخدمة التي تحتاجها؟','cat_recovery':'الوصول إلى الحساب واستعادته','cat_hacked':'التعامل مع الحساب المخترق','cat_impersonation':'انتحال الهوية والحسابات المزيفة','cat_scam':'مراجعة حادثة احتيال','cat_privacy':'الخصوصية وتسريب البيانات','cat_reputation':'حماية العلامة والسمعة','cat_compliance':'إرشاد السياسات والامتثال','cat_security':'مراجعة الأمان والوقاية','cat_other':'طلب آخر','priority_label':'مدى الاستعجال','priority_normal':'عادي','priority_high':'مرتفع','priority_critical':'حرج — حادثة مستمرة','evidence_label':'رابط الأدلة','evidence_hint':'رابط HTTPS فقط. لا ترسل كلمات مرور أو رموزاً خاصة.','story_label':'اشرح المشكلة','story_hint':'ماذا حدث ومتى بدأ وما الخطوات التي جربتها؟ اكتب 25 حرفاً على الأقل.','story_count':'حرفاً','preferred_label':'كيف تفضّل المتابعة؟','private_title':'مراجعة عبر الصندوق الخاص','private_desc':'يُحفظ ملفك لمراجعته في لوحة التحكم المحمية.','whatsapp_title':'المتابعة عبر واتساب','whatsapp_desc':'يُحفظ الملف أولاً. بعد الحفظ، اضغط زر واتساب في صفحة التأكيد لفتح رسالة جاهزة تراجعها وترسلها بنفسك.','human_label':'التحقق البشري','human_hint':'اكتب الإجابة','consent_text':'أؤكد أنني مالك الحساب أو لدي تفويض لطلب المساعدة، وأن المعلومات صحيحة حسب علمي.','privacy_note':'نستخدم هذه البيانات لتقييم طلبك والرد عليه. لا ترسل كلمات مرور أو رموز تحقق أو مفاتيح استعادة أو بيانات دفع أو وثائق غير ضرورية. مؤشرات المخاطر الآلية ليست حكماً بوجود احتيال.','submit_case':'إنشاء ملفي','secure_note':'نموذج آمن · ستحصل على رقم متابعة بعد الإرسال','services_heading':'خدمات إضافية','services_intro':'اختر الخدمة الأقرب إلى حاجتك. نراجع الوقائع قبل اقتراح الخطوات التالية.'},
'ar-tn': {'case_kicker':'طلب مساعدة آمن','case_title':'احكيلنا شنوة صار.','case_intro':'شوية تفاصيل تعاونّا نفهمو المشكلة ونوجّهو طلبك. ياخذ تقريب دقيقتين.','step_identity':'معلوماتك','step_incident':'تفاصيل المشكلة','step_next':'كيفاش نكملو','full_name':'الاسم واللقب','email_address':'الإيميل','platform_label':'المنصّة','platform_none':'موش محدّدة','handle_label':'اسم الحساب ولا رابط البروفيل','optional':'اختياري','handle_hint':'@username ولا رابط البروفيل العمومي','phone_label':'التليفون / واتساب','phone_hint':'زيد كود البلاد، مثال +216…','date_label':'وقتاش صارت المشكلة؟','date_hint':'تنجم تحط تاريخ تقريبي','category_label':'شنوة نوع المساعدة اللي تحتاجها؟','cat_recovery':'الدخول للحساب واسترجاعه','cat_hacked':'التعامل مع حساب متهكّر','cat_impersonation':'انتحال شخصية وبروفيلات مزيّفة','cat_scam':'مراجعة عملية تحيّل','cat_privacy':'الخصوصية وتسريب المعطيات','cat_reputation':'حماية الاسم والسمعة','cat_compliance':'استشارة في القوانين والسياسات','cat_security':'مراجعة الأمان والوقاية','cat_other':'حاجة أخرى','priority_label':'قدّاش الموضوع مستعجل؟','priority_normal':'عادي','priority_high':'مستعجل','priority_critical':'حرج — المشكلة مازالت متواصلة','evidence_label':'رابط الأدلة','evidence_hint':'رابط HTTPS برك. ما تبعثش كلمات سر ولا أكواد خاصّة.','story_label':'فسّرنا المشكلة','story_hint':'شنوة صار؟ وقتاش بدا؟ شنوة جرّبت تعمل؟ اكتب 25 حرف على الأقل.','story_count':'حرف','preferred_label':'كيفاش تحب نكملو؟','private_title':'مراجعة في الصندوق الخاص','private_desc':'نحفظو الملف في لوحة تحكّم محمية باش يراجعو الفريق.','whatsapp_title':'نكملو على واتساب','whatsapp_desc':'نسجّلو الملف الأول. بعد ما يتسجّل، اضغط على زر واتساب في صفحة التأكيد باش تحلّ رسالة جاهزة تراجعها وتبعثها بنفسك.','human_label':'تثبّت بشري','human_hint':'اكتب الإجابة','consent_text':'نأكد اللي الحساب متاعي ولا عندي ترخيص نطلب المساعدة، والمعلومات صحيحة حسب علمي.','privacy_note':'نستعملو المعلومات باش نقيّمو الطلب ونجاوبوك. ما تبعثش كلمة السر ولا كود التثبّت ولا مفاتيح الاسترجاع ولا معلومات الدفع. تنبيهات المخاطر الآلية تستحق مراجعة بشرية وموش حكم بالتحيّل.','submit_case':'سجّل طلبي','secure_note':'طلب آمن · يوصلك رقم متابعة بعد الإرسال','services_heading':'خدمات أخرى ننجمو نعاونوك فيها','services_intro':'اختار أقرب خدمة لمشكلتك، والفريق يراجع التفاصيل قبل الخطوة الجاية.'}
}
# Localized platform, priority and service names for the primary intake languages.
FORM_COPY['fr'].update({'platform_instagram':'Instagram','platform_facebook':'Facebook','platform_tiktok':'TikTok','platform_google':'Google','platform_x':'X','platform_linkedin':'LinkedIn','platform_other':'Autre','priority_normal':'Normal','priority_high':'Élevé','priority_critical':'Critique — incident en cours','service_1':'Accès et récupération de compte','service_1d':'Conseils via les canaux officiels, justificatifs de propriété et plan d’action.','service_2':'Réponse à un compte compromis','service_2d':'Mesures de sécurisation, contrôle des sessions et accès, chronologie des preuves.','service_3':'Usurpation et faux profils','service_3d':'Constitution des preuves, préparation du signalement et suivi.','service_4':'Analyse d’incident d’arnaque','service_4d':'Chronologie, signaux d’alerte et organisation des preuves. Aucun remboursement garanti.','service_5':'Confidentialité et fuite de données','service_5d':'Évaluation de l’exposition, sécurisation des comptes et conseils de notification.','service_6':'Protection de marque et réputation','service_6d':'Plan de surveillance, réponse à l’usurpation et recommandations.','service_7':'Conseil en règles et conformité','service_7d':'Revue des règles, préparation documentaire et accompagnement conformité.','service_8':'Audit de sécurité et prévention','service_8d':'Bonnes pratiques, authentification multifacteur et gestion des accès.'})
FORM_COPY['ar'].update({'platform_instagram':'إنستغرام','platform_facebook':'فيسبوك','platform_tiktok':'تيك توك','platform_google':'غوغل','platform_x':'إكس','platform_linkedin':'لينكدإن','platform_other':'أخرى','priority_normal':'عادي','priority_high':'مرتفع','priority_critical':'حرج — حادثة مستمرة','service_1':'الوصول إلى الحساب واستعادته','service_1d':'إرشاد عبر القنوات الرسمية وتجهيز إثبات الملكية وخطة المتابعة.','service_2':'الاستجابة لاختراق الحساب','service_2d':'خطوات الاحتواء ومراجعة الجلسات والصلاحيات وترتيب الأدلة.','service_3':'انتحال الهوية والحسابات المزيفة','service_3d':'تنظيم الأدلة وتجهيز البلاغ للمنصة ومتابعته.','service_4':'تقييم حوادث الاحتيال','service_4d':'ترتيب الأحداث ومراجعة مؤشرات الاحتيال وتنظيم الأدلة. لا نضمن استرجاع الأموال.','service_5':'الخصوصية وتسريب البيانات','service_5d':'تقييم التعرض وتأمين الحسابات وإرشادات الإبلاغ.','service_6':'حماية العلامة والسمعة','service_6d':'خطة متابعة الملفات العامة والتعامل مع الانتحال ومخاطر السمعة.','service_7':'إرشاد السياسات والامتثال','service_7d':'مراجعة السياسات وتجهيز الوثائق وإرشادات الامتثال.','service_8':'مراجعة الأمان والوقاية','service_8d':'قائمة تحسين أمان الحساب والمصادقة متعددة العوامل وإدارة الوصول.'})
FORM_COPY['ar-tn'].update({'platform_instagram':'إنستغرام','platform_facebook':'فيسبوك','platform_tiktok':'تيك توك','platform_google':'غوغل','platform_x':'إكس','platform_linkedin':'لينكدإن','platform_other':'أخرى','priority_normal':'عادي','priority_high':'مستعجل','priority_critical':'حرج — المشكلة مازالت متواصلة','service_1':'الدخول للحساب واسترجاعه','service_1d':'إرشاد عبر القنوات الرسمية وتجهيز إثبات الملكية وخطة المتابعة.','service_2':'التعامل مع حساب متهكّر','service_2d':'خطوات تأمين الحساب ومراجعة الجلسات والصلاحيات وترتيب الأدلة.','service_3':'انتحال شخصية وبروفيلات مزيّفة','service_3d':'تجميع الأدلة وتحضير التبليغ للمنصّة ومتابعته.','service_4':'تقييم حوادث التحيل','service_4d':'ترتيب الأحداث ومراجعة علامات التحيل وتنظيم الأدلة. ما نضمنوش استرجاع الفلوس.','service_5':'الخصوصية وتسريب المعطيات','service_5d':'تقييم التسريب وتأمين الحسابات وإرشادات التبليغ.','service_6':'حماية الاسم والسمعة','service_6d':'خطة متابعة البروفيلات والتعامل مع الانتحال ومخاطر السمعة.','service_7':'استشارة في السياسات والامتثال','service_7d':'مراجعة القواعد وتجهيز الوثائق وإرشادات الامتثال.','service_8':'مراجعة الأمان والوقاية','service_8d':'تحسين حماية الحساب والمصادقة الثنائية وتنظيم الصلاحيات.'})
for _code, _copy in FORM_COPY.items():
    for _obsolete_key in ('preferred_label', 'private_title', 'private_desc', 'whatsapp_title', 'whatsapp_desc', 'submit_case', 'human_label', 'human_hint'):
        _copy.pop(_obsolete_key, None)
    LANGS[_code].update(_copy)

# One single submit action: validate, save the case, then redirect directly to WhatsApp.
WHATSAPP_INTAKE_COPY = {
    'en': {'step_next':'CREATE CASE', 'create_secure_case':'Create secure case', 'secure_note':'Your case is saved first. The next page lets you review the reference and open WhatsApp with the complete report.', 'case_ready_title':'Your secure case is saved', 'case_ready_intro':'Your information has been saved in the case desk. Use the button below to open WhatsApp with the complete report already prepared.', 'case_ready_reference':'Case reference', 'case_ready_status':'Saved securely', 'case_ready_send':'Send to WhatsApp', 'case_ready_note':'WhatsApp will open with the full case details and review report filled in. Check the message and press Send inside WhatsApp.', 'whatsapp_configuration_error':'WhatsApp is not configured correctly. Your case has not been created. Please contact the site administrator.'},
    'fr': {'step_next':'CRÉER LE DOSSIER', 'create_secure_case':'Créer le dossier sécurisé', 'secure_note':'Votre dossier est d’abord enregistré. La page suivante affiche sa référence et permet d’ouvrir WhatsApp avec le rapport complet.', 'case_ready_title':'Votre dossier sécurisé est enregistré', 'case_ready_intro':'Vos informations ont été enregistrées. Utilisez le bouton ci-dessous pour ouvrir WhatsApp avec le rapport complet déjà préparé.', 'case_ready_reference':'Référence du dossier', 'case_ready_status':'Enregistré en toute sécurité', 'case_ready_send':'Envoyer sur WhatsApp', 'case_ready_note':'WhatsApp s’ouvrira avec les détails et le rapport complet. Vérifiez le message puis appuyez sur Envoyer dans WhatsApp.', 'whatsapp_configuration_error':'WhatsApp n’est pas correctement configuré. Votre dossier n’a pas été créé. Contactez l’administrateur du site.'},
    'ar': {'step_next':'إنشاء الملف', 'create_secure_case':'إنشاء ملف آمن', 'secure_note':'يتم حفظ ملفك أولاً. تعرض الصفحة التالية رقم الملف وتتيح فتح واتساب مع التقرير الكامل.', 'case_ready_title':'تم حفظ ملفك الآمن', 'case_ready_intro':'تم حفظ معلوماتك في النظام. استخدم الزر أدناه لفتح واتساب مع التقرير الكامل المُعد مسبقاً.', 'case_ready_reference':'رقم الملف', 'case_ready_status':'تم الحفظ بأمان', 'case_ready_send':'إرسال عبر واتساب', 'case_ready_note':'سيفتح واتساب مع جميع تفاصيل الملف والتقرير. راجع الرسالة ثم اضغط إرسال داخل واتساب.', 'whatsapp_configuration_error':'واتساب غير مُهيأ بشكل صحيح. لم يتم إنشاء ملفك. يرجى التواصل مع مسؤول الموقع.'},
    'ar-tn': {'step_next':'سجّل الملف', 'create_secure_case':'سجّل ملف آمن', 'secure_note':'أول حاجة نسجّلو الملف. الصفحة الثانية توريك رقم الملف وتفتحلك واتساب برسالة فيها التقرير الكل.', 'case_ready_title':'الملف الآمن متاعك تسجّل', 'case_ready_intro':'معلوماتك تسجّلت في النظام. اضغط على الزر لتفتح واتساب برسالة محضّرة فيها التقرير والتفاصيل الكل.', 'case_ready_reference':'رقم الملف', 'case_ready_status':'تسجّل بأمان', 'case_ready_send':'ابعث عبر واتساب', 'case_ready_note':'واتساب يتحلّ والرسالة فيها تفاصيل الملف والتقرير. راجعها وبعد اضغط إرسال من داخل واتساب.', 'whatsapp_configuration_error':'واتساب موش مهيّأ بطريقة صحيحة. الملف متاعك ما تسجّلش. اتصل بمسؤول الموقع.'},
    'es': {'step_next':'CREAR CASO', 'create_secure_case':'Crear caso seguro', 'secure_note':'Primero se guarda tu caso. La página siguiente muestra la referencia y permite abrir WhatsApp con el informe completo.', 'case_ready_title':'Tu caso seguro está guardado', 'case_ready_intro':'Tu información se ha guardado. Usa el botón siguiente para abrir WhatsApp con el informe completo preparado.', 'case_ready_reference':'Referencia del caso', 'case_ready_status':'Guardado de forma segura', 'case_ready_send':'Enviar por WhatsApp', 'case_ready_note':'WhatsApp se abrirá con todos los detalles y el informe. Revisa el mensaje y pulsa Enviar dentro de WhatsApp.', 'whatsapp_configuration_error':'WhatsApp no está configurado correctamente. No se ha creado el caso. Contacta con el administrador del sitio.'},
    'de': {'step_next':'FALL ERSTELLEN', 'create_secure_case':'Sicheren Fall erstellen', 'secure_note':'Zuerst wird dein Fall gespeichert. Auf der nächsten Seite siehst du die Referenz und kannst WhatsApp mit dem vollständigen Bericht öffnen.', 'case_ready_title':'Dein sicherer Fall wurde gespeichert', 'case_ready_intro':'Deine Angaben wurden gespeichert. Öffne über die Schaltfläche WhatsApp mit dem vorbereiteten vollständigen Bericht.', 'case_ready_reference':'Fallreferenz', 'case_ready_status':'Sicher gespeichert', 'case_ready_send':'An WhatsApp senden', 'case_ready_note':'WhatsApp öffnet sich mit allen Falldetails und dem Bericht. Prüfe die Nachricht und drücke in WhatsApp auf Senden.', 'whatsapp_configuration_error':'WhatsApp ist nicht korrekt konfiguriert. Dein Fall wurde nicht erstellt. Bitte kontaktiere den Website-Administrator.'},
    'it': {'step_next':'CREA CASO', 'create_secure_case':'Crea caso sicuro', 'secure_note':'Prima il caso viene salvato. La pagina successiva mostra il riferimento e permette di aprire WhatsApp con il rapporto completo.', 'case_ready_title':'Il tuo caso sicuro è stato salvato', 'case_ready_intro':'Le tue informazioni sono state salvate. Usa il pulsante seguente per aprire WhatsApp con il rapporto completo già preparato.', 'case_ready_reference':'Riferimento del caso', 'case_ready_status':'Salvato in sicurezza', 'case_ready_send':'Invia su WhatsApp', 'case_ready_note':'WhatsApp si aprirà con tutti i dettagli e il rapporto. Controlla il messaggio e premi Invia dentro WhatsApp.', 'whatsapp_configuration_error':'WhatsApp non è configurato correttamente. Il caso non è stato creato. Contatta l’amministratore del sito.'},
    'pt': {'step_next':'CRIAR CASO', 'create_secure_case':'Criar caso seguro', 'secure_note':'O caso é guardado primeiro. A página seguinte mostra a referência e permite abrir o WhatsApp com o relatório completo.', 'case_ready_title':'O seu caso seguro foi guardado', 'case_ready_intro':'As suas informações foram guardadas. Use o botão abaixo para abrir o WhatsApp com o relatório completo preparado.', 'case_ready_reference':'Referência do caso', 'case_ready_status':'Guardado em segurança', 'case_ready_send':'Enviar pelo WhatsApp', 'case_ready_note':'O WhatsApp abrirá com todos os detalhes e o relatório. Reveja a mensagem e prima Enviar no WhatsApp.', 'whatsapp_configuration_error':'O WhatsApp não está corretamente configurado. O caso não foi criado. Contacte o administrador do site.'},
    'tr': {'step_next':'DOSYA OLUŞTUR', 'create_secure_case':'Güvenli dosya oluştur', 'secure_note':'Önce dosyanız kaydedilir. Sonraki sayfada referansı görür ve tam rapor hazır şekilde WhatsApp’ı açabilirsiniz.', 'case_ready_title':'Güvenli dosyanız kaydedildi', 'case_ready_intro':'Bilgileriniz kaydedildi. Tam rapor hazırlanmış olarak WhatsApp’ı açmak için aşağıdaki düğmeyi kullanın.', 'case_ready_reference':'Dosya referansı', 'case_ready_status':'Güvenle kaydedildi', 'case_ready_send':'WhatsApp ile gönder', 'case_ready_note':'WhatsApp tüm dosya ayrıntıları ve raporla açılır. Mesajı kontrol edin ve WhatsApp içinde Gönder’e basın.', 'whatsapp_configuration_error':'WhatsApp doğru yapılandırılmamış. Dosyanız oluşturulmadı. Lütfen site yöneticisiyle iletişime geçin.'},
    'zh': {'step_next':'创建案件', 'create_secure_case':'创建安全案件', 'secure_note':'系统会先保存案件。下一页会显示案件编号，并可打开已填入完整报告的 WhatsApp。', 'case_ready_title':'您的安全案件已保存', 'case_ready_intro':'您的信息已保存。点击下方按钮即可打开已准备好完整报告的 WhatsApp。', 'case_ready_reference':'案件编号', 'case_ready_status':'已安全保存', 'case_ready_send':'发送至 WhatsApp', 'case_ready_note':'WhatsApp 将打开并填入完整案件详情及报告。请检查消息，然后在 WhatsApp 中点击发送。', 'whatsapp_configuration_error':'WhatsApp 配置不正确。案件尚未创建。请联系网站管理员。'},
    'ja': {'step_next':'ケースを作成', 'create_secure_case':'安全なケースを作成', 'secure_note':'最初にケースを保存します。次のページで参照番号を確認し、完全なレポートが入力された WhatsApp を開けます。', 'case_ready_title':'安全なケースを保存しました', 'case_ready_intro':'情報はケースデスクに保存されました。下のボタンから、完全なレポートが準備された WhatsApp を開いてください。', 'case_ready_reference':'ケース参照番号', 'case_ready_status':'安全に保存済み', 'case_ready_send':'WhatsAppで送信', 'case_ready_note':'WhatsApp にケースの詳細とレポートが入力されます。内容を確認して WhatsApp 内で送信を押してください。', 'whatsapp_configuration_error':'WhatsApp が正しく設定されていません。ケースは作成されていません。サイト管理者に連絡してください。'},
}
for _locale, _labels in WHATSAPP_INTAKE_COPY.items():
    LANGS[_locale].update(_labels)
    for _obsolete_key in ('preferred_label', 'private_title', 'private_desc', 'whatsapp_title', 'whatsapp_desc', 'submit_case', 'human_label', 'human_hint'):
        LANGS[_locale].pop(_obsolete_key, None)

# Translations for the case dashboard, case report and receipt screens.
ADMIN_COPY = {'en': {'admin_title': 'Case intelligence', 'admin_subtitle': 'Private workspace · Review evidence and context before deciding. Automated risk flags are not verdicts.', 'internal': 'INTERNAL / CASE OPERATIONS', 'total_cases': 'TOTAL CASES', 'latest_records': 'Latest 250 records', 'new_waiting': 'Awaiting first review', 'in_review': 'IN REVIEW', 'active_assessment': 'Active assessment', 'priority_flags': 'PRIORITY FLAGS', 'human_triage': 'Human triage required', 'recent_submissions': 'Recent submissions', 'newest_first': 'Newest first · UTC timestamps', 'case_requester': 'Case / requester', 'category': 'Category', 'priority': 'Priority', 'review_indicators': 'Review indicators', 'received': 'Received', 'action': 'Action', 'no_indicators': 'No indicators', 'open_report': 'Open report', 'back_all': 'All cases', 'confidential_report': 'CONFIDENTIAL / CASE REPORT', 'export_csv': 'Export CSV', 'export_all': 'Export all CSV', 'requester_incident': 'Requester & incident', 'name': 'Name', 'email': 'Email', 'phone': 'Phone', 'not_provided': 'Not provided', 'platform': 'Platform', 'account_handle': 'Account handle', 'incident_date': 'Incident date', 'evidence_link': 'Evidence link', 'open_supplied': 'Open supplied link', 'not_supplied': 'Not supplied', 'intake_triage': 'Intake triage', 'indicator_score': 'Indicator score', 'advisory_only': 'advisory only', 'matched_indicators': 'Matched indicators', 'none_detected': 'None detected by configured checks', 'original_report': 'Original report', 'case_management': 'Case management', 'case_status': 'Case status', 'save_status': 'Save case status', 'submitted_title': 'Case created.', 'submitted_desc': 'Your report has been recorded. Keep this reference for follow-up.', 'receipt_notice': 'A case reference confirms receipt only; it does not mean that an investigation has concluded or that fraud has been established.', 'return_home': 'Return to home', 'intake_confirmed': 'INTAKE CONFIRMED / 02', 'received_at': 'Received', 'case_created': 'Case created successfully', 'whatsapp_unavailable': 'WhatsApp hand-off is not configured. Your case has still been saved. Please use the contact details on the website.', 'login_subtitle': 'Restricted access. Only authorized team members can view submitted messages.'}, 'fr': {'admin_title': 'Dossiers et signalements', 'admin_subtitle': 'Espace privé · Examinez les éléments et leur contexte avant toute décision. Les alertes automatisées ne constituent pas un verdict.', 'internal': 'INTERNE / GESTION DES DOSSIERS', 'total_cases': 'TOTAL DES DOSSIERS', 'latest_records': '250 dossiers les plus récents', 'new_waiting': 'En attente du premier examen', 'in_review': 'EN COURS', 'active_assessment': 'Évaluation active', 'priority_flags': 'ALERTES DE PRIORITÉ', 'human_triage': 'Examen humain requis', 'recent_submissions': 'Demandes récentes', 'newest_first': 'Plus récent en premier · heures UTC', 'case_requester': 'Dossier / demandeur', 'category': 'Catégorie', 'priority': 'Priorité', 'review_indicators': 'Indicateurs à examiner', 'received': 'Reçu', 'action': 'Action', 'no_indicators': 'Aucun indicateur', 'open_report': 'Ouvrir le rapport', 'back_all': 'Tous les dossiers', 'confidential_report': 'CONFIDENTIEL / RAPPORT DE DOSSIER', 'export_csv': 'Exporter CSV', 'export_all': 'Tout exporter en CSV', 'requester_incident': 'Demandeur et incident', 'name': 'Nom', 'email': 'E-mail', 'phone': 'Téléphone', 'not_provided': 'Non renseigné', 'platform': 'Plateforme', 'account_handle': 'Identifiant du compte', 'incident_date': 'Date de l’incident', 'evidence_link': 'Lien vers les preuves', 'open_supplied': 'Ouvrir le lien fourni', 'not_supplied': 'Non fourni', 'intake_triage': 'Tri initial', 'indicator_score': 'Score indicatif', 'advisory_only': 'indicatif uniquement', 'matched_indicators': 'Indicateurs détectés', 'none_detected': 'Aucun indicateur détecté par les règles configurées', 'original_report': 'Signalement original', 'case_management': 'Gestion du dossier', 'case_status': 'Statut du dossier', 'save_status': 'Enregistrer le statut', 'submitted_title': 'Dossier créé.', 'submitted_desc': 'Votre signalement a été enregistré. Conservez cette référence pour le suivi.', 'receipt_notice': 'La référence confirme uniquement la réception. Elle ne signifie pas qu’une enquête est terminée ni qu’une fraude est établie.', 'return_home': 'Retour à l’accueil', 'intake_confirmed': 'DEMANDE CONFIRMÉE / 02', 'received_at': 'Reçu le', 'case_created': 'Dossier créé avec succès', 'whatsapp_unavailable': 'Le transfert WhatsApp n’est pas configuré. Votre dossier a bien été enregistré. Utilisez les coordonnées du site.', 'login_subtitle': 'Accès réservé aux membres autorisés de l’équipe.'}, 'ar': {'admin_title': 'إدارة الملفات', 'admin_subtitle': 'مساحة خاصة · راجع الأدلة والسياق قبل اتخاذ القرار. التنبيهات الآلية ليست حكماً نهائياً.', 'internal': 'داخلي / إدارة الملفات', 'total_cases': 'إجمالي الملفات', 'latest_records': 'أحدث 250 ملفاً', 'new_waiting': 'بانتظار المراجعة الأولى', 'in_review': 'قيد المراجعة', 'active_assessment': 'تقييم جارٍ', 'priority_flags': 'مؤشرات الأولوية', 'human_triage': 'تتطلب مراجعة بشرية', 'recent_submissions': 'أحدث الطلبات', 'newest_first': 'الأحدث أولاً · التوقيت العالمي UTC', 'case_requester': 'الملف / صاحب الطلب', 'category': 'الفئة', 'priority': 'الأولوية', 'review_indicators': 'مؤشرات للمراجعة', 'received': 'تاريخ الاستلام', 'action': 'الإجراء', 'no_indicators': 'لا توجد مؤشرات', 'open_report': 'فتح التقرير', 'back_all': 'كل الملفات', 'confidential_report': 'سري / تقرير الملف', 'export_csv': 'تصدير CSV', 'export_all': 'تصدير الكل CSV', 'requester_incident': 'مقدم الطلب والحادثة', 'name': 'الاسم', 'email': 'البريد الإلكتروني', 'phone': 'الهاتف', 'not_provided': 'غير مقدم', 'platform': 'المنصة', 'account_handle': 'اسم الحساب', 'incident_date': 'تاريخ الحادثة', 'evidence_link': 'رابط الأدلة', 'open_supplied': 'فتح الرابط المقدم', 'not_supplied': 'غير مقدم', 'intake_triage': 'فرز الطلب', 'indicator_score': 'درجة المؤشرات', 'advisory_only': 'استرشادي فقط', 'matched_indicators': 'المؤشرات المطابقة', 'none_detected': 'لم ترصد القواعد المحددة أي مؤشرات', 'original_report': 'البلاغ الأصلي', 'case_management': 'إدارة الملف', 'case_status': 'حالة الملف', 'save_status': 'حفظ الحالة', 'submitted_title': 'تم إنشاء الملف.', 'submitted_desc': 'تم حفظ بلاغك. احتفظ بهذا الرقم للمتابعة.', 'receipt_notice': 'رقم الملف يؤكد الاستلام فقط، ولا يعني انتهاء التحقيق أو ثبوت الاحتيال.', 'return_home': 'العودة إلى الرئيسية', 'intake_confirmed': 'تم تأكيد الطلب / 02', 'received_at': 'تاريخ الاستلام', 'case_created': 'تم إنشاء الملف بنجاح', 'whatsapp_unavailable': 'لم يتم إعداد واتساب. تم حفظ ملفك بنجاح. يرجى استخدام بيانات التواصل الموجودة في الموقع.', 'login_subtitle': 'الدخول مخصص لأعضاء الفريق المخولين فقط.'}, 'ar-tn': {'admin_title': 'إدارة الملفات', 'admin_subtitle': 'فضاء خاص · راجع الأدلة والسياق قبل ما تاخو قرار. التنبيهات الآلية موش حكم نهائي.', 'internal': 'داخلي / إدارة الملفات', 'total_cases': 'مجموع الملفات', 'latest_records': 'آخر 250 ملف', 'new_waiting': 'يستنى في أول مراجعة', 'in_review': 'قيد المراجعة', 'active_assessment': 'التقييم متواصل', 'priority_flags': 'تنبيهات الأولوية', 'human_triage': 'يلزم مراجعة بشرية', 'recent_submissions': 'آخر الطلبات', 'newest_first': 'الجديد قبل · توقيت UTC', 'case_requester': 'الملف / صاحب الطلب', 'category': 'الصنف', 'priority': 'الأولوية', 'review_indicators': 'مؤشرات للمراجعة', 'received': 'وقت الاستلام', 'action': 'الإجراء', 'no_indicators': 'ما فماش مؤشرات', 'open_report': 'افتح التقرير', 'back_all': 'كل الملفات', 'confidential_report': 'سري / تقرير الملف', 'export_csv': 'تصدير CSV', 'export_all': 'تصدير الكل CSV', 'requester_incident': 'صاحب الطلب والحادثة', 'name': 'الاسم', 'email': 'الإيميل', 'phone': 'التليفون', 'not_provided': 'موش موجود', 'platform': 'المنصة', 'account_handle': 'اسم الحساب', 'incident_date': 'تاريخ الحادثة', 'evidence_link': 'رابط الأدلة', 'open_supplied': 'افتح الرابط', 'not_supplied': 'موش موجود', 'intake_triage': 'فرز الطلب', 'indicator_score': 'درجة المؤشرات', 'advisory_only': 'للاسترشاد فقط', 'matched_indicators': 'المؤشرات الموجودة', 'none_detected': 'القواعد ما لقات حتى مؤشر', 'original_report': 'البلاغ الأصلي', 'case_management': 'إدارة الملف', 'case_status': 'حالة الملف', 'save_status': 'احفظ الحالة', 'submitted_title': 'تسجّل الملف.', 'submitted_desc': 'تسجّل البلاغ متاعك. احتفظ بالرقم هذا للمتابعة.', 'receipt_notice': 'رقم الملف يأكد الاستلام برك، وما يعنيش اللي التحقيق وفى ولا اللي التحيل ثبت.', 'return_home': 'ارجع للرئيسية', 'intake_confirmed': 'تأكيد الطلب / 02', 'received_at': 'وقت الاستلام', 'case_created': 'تسجّل الملف بنجاح', 'whatsapp_unavailable': 'واتساب موش مهيّأ. الملف متاعك تسجّل بنجاح. استعمل معلومات الاتصال الموجودة في الموقع.', 'login_subtitle': 'الدخول كان لأعضاء الفريق المرخّص لهم.'}, 'es': {'admin_title': 'Gestión de casos', 'admin_subtitle': 'Espacio privado · Revise las pruebas y el contexto antes de decidir. Las alertas automáticas no son veredictos.', 'internal': 'INTERNO / OPERACIONES DE CASOS', 'total_cases': 'CASOS TOTALES', 'latest_records': 'Últimos 250 registros', 'new_waiting': 'Pendiente de primera revisión', 'in_review': 'EN REVISIÓN', 'active_assessment': 'Evaluación activa', 'priority_flags': 'ALERTAS DE PRIORIDAD', 'human_triage': 'Requiere revisión humana', 'recent_submissions': 'Solicitudes recientes', 'newest_first': 'Más recientes primero · UTC', 'case_requester': 'Caso / solicitante', 'category': 'Categoría', 'priority': 'Prioridad', 'review_indicators': 'Indicadores de revisión', 'received': 'Recibido', 'action': 'Acción', 'no_indicators': 'Sin indicadores', 'open_report': 'Abrir informe', 'back_all': 'Todos los casos', 'confidential_report': 'CONFIDENCIAL / INFORME DEL CASO', 'export_csv': 'Exportar CSV', 'export_all': 'Exportar todo CSV', 'requester_incident': 'Solicitante e incidente', 'name': 'Nombre', 'email': 'Correo', 'phone': 'Teléfono', 'not_provided': 'No indicado', 'platform': 'Plataforma', 'account_handle': 'Usuario de la cuenta', 'incident_date': 'Fecha del incidente', 'evidence_link': 'Enlace de pruebas', 'open_supplied': 'Abrir enlace facilitado', 'not_supplied': 'No facilitado', 'intake_triage': 'Clasificación inicial', 'indicator_score': 'Puntuación indicativa', 'advisory_only': 'solo orientativo', 'matched_indicators': 'Indicadores coincidentes', 'none_detected': 'No se detectaron indicadores configurados', 'original_report': 'Informe original', 'case_management': 'Gestión del caso', 'case_status': 'Estado del caso', 'save_status': 'Guardar estado', 'submitted_title': 'Caso creado.', 'submitted_desc': 'Su informe se ha registrado. Guarde esta referencia para el seguimiento.', 'receipt_notice': 'La referencia solo confirma la recepción; no significa que la investigación haya concluido ni que se haya demostrado fraude.', 'return_home': 'Volver al inicio', 'intake_confirmed': 'SOLICITUD CONFIRMADA / 02', 'received_at': 'Recibido', 'case_created': 'Caso creado correctamente', 'whatsapp_unavailable': 'WhatsApp no está configurado. Su caso se ha guardado. Use los datos de contacto del sitio.', 'login_subtitle': 'Acceso restringido a miembros autorizados del equipo.'}, 'de': {'admin_title': 'Fallverwaltung', 'admin_subtitle': 'Privater Bereich · Prüfen Sie Belege und Kontext vor einer Entscheidung. Automatische Risikohinweise sind keine Urteile.', 'internal': 'INTERN / FALLVERWALTUNG', 'total_cases': 'FÄLLE GESAMT', 'latest_records': 'Letzte 250 Einträge', 'new_waiting': 'Wartet auf erste Prüfung', 'in_review': 'IN PRÜFUNG', 'active_assessment': 'Aktive Bewertung', 'priority_flags': 'PRIORITÄTSHINWEISE', 'human_triage': 'Menschliche Prüfung erforderlich', 'recent_submissions': 'Neueste Anfragen', 'newest_first': 'Neueste zuerst · UTC', 'case_requester': 'Fall / anfragende Person', 'category': 'Kategorie', 'priority': 'Priorität', 'review_indicators': 'Prüfindikatoren', 'received': 'Eingegangen', 'action': 'Aktion', 'no_indicators': 'Keine Indikatoren', 'open_report': 'Bericht öffnen', 'back_all': 'Alle Fälle', 'confidential_report': 'VERTRAULICH / FALLBERICHT', 'export_csv': 'CSV exportieren', 'export_all': 'Alle als CSV exportieren', 'requester_incident': 'Anfragende Person und Vorfall', 'name': 'Name', 'email': 'E-Mail', 'phone': 'Telefon', 'not_provided': 'Nicht angegeben', 'platform': 'Plattform', 'account_handle': 'Konto-Kennung', 'incident_date': 'Vorfallsdatum', 'evidence_link': 'Beweislink', 'open_supplied': 'Angegebenen Link öffnen', 'not_supplied': 'Nicht angegeben', 'intake_triage': 'Ersteinstufung', 'indicator_score': 'Hinweiswert', 'advisory_only': 'nur ein Hinweis', 'matched_indicators': 'Erkannte Hinweise', 'none_detected': 'Keine konfigurierten Hinweise erkannt', 'original_report': 'Ursprüngliche Meldung', 'case_management': 'Fallverwaltung', 'case_status': 'Fallstatus', 'save_status': 'Status speichern', 'submitted_title': 'Fall erstellt.', 'submitted_desc': 'Ihre Meldung wurde gespeichert. Bewahren Sie diese Referenz zur Nachverfolgung auf.', 'receipt_notice': 'Die Referenz bestätigt nur den Eingang. Sie bedeutet weder einen abgeschlossenen Vorgang noch einen nachgewiesenen Betrug.', 'return_home': 'Zur Startseite', 'intake_confirmed': 'EINGANG BESTÄTIGT / 02', 'received_at': 'Eingegangen am', 'case_created': 'Fall erfolgreich erstellt', 'whatsapp_unavailable': 'WhatsApp ist nicht konfiguriert. Ihr Fall wurde trotzdem gespeichert. Nutzen Sie die Kontaktangaben auf der Website.', 'login_subtitle': 'Nur autorisierte Teammitglieder dürfen eingereichte Nachrichten ansehen.'}, 'it': {'admin_title': 'Gestione pratiche', 'admin_subtitle': 'Area privata · Esamina prove e contesto prima di decidere. Gli avvisi automatici non sono verdetti.', 'internal': 'INTERNO / GESTIONE PRATICHE', 'total_cases': 'PRATICHE TOTALI', 'latest_records': 'Ultimi 250 record', 'new_waiting': 'In attesa della prima revisione', 'in_review': 'IN REVISIONE', 'active_assessment': 'Valutazione attiva', 'priority_flags': 'AVVISI DI PRIORITÀ', 'human_triage': 'Richiede revisione umana', 'recent_submissions': 'Richieste recenti', 'newest_first': 'Più recenti prima · UTC', 'case_requester': 'Pratica / richiedente', 'category': 'Categoria', 'priority': 'Priorità', 'review_indicators': 'Indicatori da verificare', 'received': 'Ricevuto', 'action': 'Azione', 'no_indicators': 'Nessun indicatore', 'open_report': 'Apri rapporto', 'back_all': 'Tutte le pratiche', 'confidential_report': 'RISERVATO / RAPPORTO PRATICA', 'export_csv': 'Esporta CSV', 'export_all': 'Esporta tutto CSV', 'requester_incident': 'Richiedente e incidente', 'name': 'Nome', 'email': 'Email', 'phone': 'Telefono', 'not_provided': 'Non fornito', 'platform': 'Piattaforma', 'account_handle': 'Nome account', 'incident_date': 'Data incidente', 'evidence_link': 'Link alle prove', 'open_supplied': 'Apri link fornito', 'not_supplied': 'Non fornito', 'intake_triage': 'Valutazione iniziale', 'indicator_score': 'Punteggio indicativo', 'advisory_only': 'solo indicativo', 'matched_indicators': 'Indicatori rilevati', 'none_detected': 'Nessun indicatore configurato rilevato', 'original_report': 'Segnalazione originale', 'case_management': 'Gestione pratica', 'case_status': 'Stato pratica', 'save_status': 'Salva stato', 'submitted_title': 'Pratica creata.', 'submitted_desc': 'La segnalazione è stata registrata. Conserva questo riferimento per il seguito.', 'receipt_notice': 'Il riferimento conferma solo la ricezione; non significa che un’indagine sia conclusa o che una frode sia stata accertata.', 'return_home': 'Torna alla home', 'intake_confirmed': 'RICHIESTA CONFERMATA / 02', 'received_at': 'Ricevuto', 'case_created': 'Pratica creata correttamente', 'whatsapp_unavailable': 'WhatsApp non è configurato. La pratica è stata comunque salvata. Usa i contatti sul sito.', 'login_subtitle': 'Accesso riservato ai membri autorizzati del team.'}, 'pt': {'admin_title': 'Gestão de casos', 'admin_subtitle': 'Área privada · Analise as provas e o contexto antes de decidir. Alertas automáticos não são veredictos.', 'internal': 'INTERNO / OPERAÇÕES DE CASOS', 'total_cases': 'TOTAL DE CASOS', 'latest_records': 'Últimos 250 registos', 'new_waiting': 'Aguardando primeira análise', 'in_review': 'EM ANÁLISE', 'active_assessment': 'Avaliação ativa', 'priority_flags': 'ALERTAS DE PRIORIDADE', 'human_triage': 'Requer análise humana', 'recent_submissions': 'Pedidos recentes', 'newest_first': 'Mais recentes primeiro · UTC', 'case_requester': 'Caso / solicitante', 'category': 'Categoria', 'priority': 'Prioridade', 'review_indicators': 'Indicadores para análise', 'received': 'Recebido', 'action': 'Ação', 'no_indicators': 'Sem indicadores', 'open_report': 'Abrir relatório', 'back_all': 'Todos os casos', 'confidential_report': 'CONFIDENCIAL / RELATÓRIO DO CASO', 'export_csv': 'Exportar CSV', 'export_all': 'Exportar tudo em CSV', 'requester_incident': 'Solicitante e incidente', 'name': 'Nome', 'email': 'E-mail', 'phone': 'Telefone', 'not_provided': 'Não fornecido', 'platform': 'Plataforma', 'account_handle': 'Identificador da conta', 'incident_date': 'Data do incidente', 'evidence_link': 'Link das provas', 'open_supplied': 'Abrir link fornecido', 'not_supplied': 'Não fornecido', 'intake_triage': 'Triagem inicial', 'indicator_score': 'Pontuação indicativa', 'advisory_only': 'apenas indicativa', 'matched_indicators': 'Indicadores encontrados', 'none_detected': 'Nenhum indicador configurado foi detetado', 'original_report': 'Relato original', 'case_management': 'Gestão do caso', 'case_status': 'Estado do caso', 'save_status': 'Guardar estado', 'submitted_title': 'Caso criado.', 'submitted_desc': 'O seu relato foi registado. Guarde esta referência para acompanhamento.', 'receipt_notice': 'A referência confirma apenas a receção; não significa que a investigação terminou ou que uma fraude foi comprovada.', 'return_home': 'Voltar ao início', 'intake_confirmed': 'PEDIDO CONFIRMADO / 02', 'received_at': 'Recebido', 'case_created': 'Caso criado com sucesso', 'whatsapp_unavailable': 'O WhatsApp não está configurado. O caso foi guardado. Utilize os contactos do site.', 'login_subtitle': 'Acesso restrito aos membros autorizados da equipa.'}, 'tr': {'admin_title': 'Dosya yönetimi', 'admin_subtitle': 'Özel alan · Karar vermeden önce kanıtları ve bağlamı inceleyin. Otomatik risk uyarıları kesin hüküm değildir.', 'internal': 'DAHİLİ / DOSYA İŞLEMLERİ', 'total_cases': 'TOPLAM DOSYA', 'latest_records': 'Son 250 kayıt', 'new_waiting': 'İlk inceleme bekliyor', 'in_review': 'İNCELEMEDE', 'active_assessment': 'Değerlendirme sürüyor', 'priority_flags': 'ÖNCELİK UYARILARI', 'human_triage': 'İnsan incelemesi gerekli', 'recent_submissions': 'Son başvurular', 'newest_first': 'En yeni önce · UTC', 'case_requester': 'Dosya / başvuran', 'category': 'Kategori', 'priority': 'Öncelik', 'review_indicators': 'İnceleme göstergeleri', 'received': 'Alındı', 'action': 'İşlem', 'no_indicators': 'Gösterge yok', 'open_report': 'Raporu aç', 'back_all': 'Tüm dosyalar', 'confidential_report': 'GİZLİ / DOSYA RAPORU', 'export_csv': 'CSV dışa aktar', 'export_all': 'Tümünü CSV dışa aktar', 'requester_incident': 'Başvuran ve olay', 'name': 'Ad', 'email': 'E-posta', 'phone': 'Telefon', 'not_provided': 'Belirtilmedi', 'platform': 'Platform', 'account_handle': 'Hesap adı', 'incident_date': 'Olay tarihi', 'evidence_link': 'Kanıt bağlantısı', 'open_supplied': 'Verilen bağlantıyı aç', 'not_supplied': 'Sağlanmadı', 'intake_triage': 'İlk değerlendirme', 'indicator_score': 'Gösterge puanı', 'advisory_only': 'yalnızca tavsiye niteliğinde', 'matched_indicators': 'Eşleşen göstergeler', 'none_detected': 'Yapılandırılmış kontrollerde gösterge bulunmadı', 'original_report': 'Orijinal bildirim', 'case_management': 'Dosya yönetimi', 'case_status': 'Dosya durumu', 'save_status': 'Durumu kaydet', 'submitted_title': 'Dosya oluşturuldu.', 'submitted_desc': 'Bildiriminiz kaydedildi. Takip için bu referansı saklayın.', 'receipt_notice': 'Referans yalnızca alındıyı doğrular; soruşturmanın tamamlandığı veya dolandırıcılığın kanıtlandığı anlamına gelmez.', 'return_home': 'Ana sayfaya dön', 'intake_confirmed': 'BAŞVURU ONAYLANDI / 02', 'received_at': 'Alınma zamanı', 'case_created': 'Dosya başarıyla oluşturuldu', 'whatsapp_unavailable': 'WhatsApp yapılandırılmamış. Dosyanız yine de kaydedildi. Lütfen sitedeki iletişim bilgilerini kullanın.', 'login_subtitle': 'Yalnızca yetkili ekip üyeleri gönderilen mesajları görebilir.'}, 'zh': {'admin_title': '案件管理', 'admin_subtitle': '私人工作区 · 决策前请检查证据和背景。自动风险提示不代表最终结论。', 'internal': '内部 / 案件处理', 'total_cases': '案件总数', 'latest_records': '最近 250 条记录', 'new_waiting': '等待首次审核', 'in_review': '审核中', 'active_assessment': '正在评估', 'priority_flags': '优先级提示', 'human_triage': '需要人工审核', 'recent_submissions': '最新提交', 'newest_first': '最新优先 · UTC 时间', 'case_requester': '案件 / 申请人', 'category': '类别', 'priority': '优先级', 'review_indicators': '审核指标', 'received': '接收时间', 'action': '操作', 'no_indicators': '无指标', 'open_report': '打开报告', 'back_all': '所有案件', 'confidential_report': '机密 / 案件报告', 'export_csv': '导出 CSV', 'export_all': '导出全部 CSV', 'requester_incident': '申请人与事件', 'name': '姓名', 'email': '电子邮件', 'phone': '电话', 'not_provided': '未提供', 'platform': '平台', 'account_handle': '账户名称', 'incident_date': '事件日期', 'evidence_link': '证据链接', 'open_supplied': '打开提供的链接', 'not_supplied': '未提供', 'intake_triage': '初步分流', 'indicator_score': '指标分数', 'advisory_only': '仅供参考', 'matched_indicators': '匹配指标', 'none_detected': '未检测到已配置指标', 'original_report': '原始报告', 'case_management': '案件管理', 'case_status': '案件状态', 'save_status': '保存状态', 'submitted_title': '案件已创建。', 'submitted_desc': '您的报告已记录。请保存此编号以便后续跟进。', 'receipt_notice': '案件编号仅确认已收到报告，并不表示调查已结束或欺诈已被证实。', 'return_home': '返回首页', 'intake_confirmed': '已确认提交 / 02', 'received_at': '接收时间', 'case_created': '案件创建成功', 'whatsapp_unavailable': '尚未配置 WhatsApp。您的案件仍已保存。请使用网站上的联系方式。', 'login_subtitle': '仅授权团队成员可以查看提交的信息。'}, 'ja': {'admin_title': '案件管理', 'admin_subtitle': '非公開ワークスペース · 判断前に証拠と背景を確認してください。自動リスク通知は断定ではありません。', 'internal': '内部 / 案件業務', 'total_cases': '案件総数', 'latest_records': '最新250件', 'new_waiting': '初回確認待ち', 'in_review': '確認中', 'active_assessment': '評価中', 'priority_flags': '優先度アラート', 'human_triage': '担当者による確認が必要', 'recent_submissions': '最近の申請', 'newest_first': '新しい順 · UTC', 'case_requester': '案件 / 申請者', 'category': 'カテゴリ', 'priority': '優先度', 'review_indicators': '確認指標', 'received': '受信日時', 'action': '操作', 'no_indicators': '指標なし', 'open_report': 'レポートを開く', 'back_all': 'すべての案件', 'confidential_report': '機密 / 案件レポート', 'export_csv': 'CSVをエクスポート', 'export_all': 'すべてCSVでエクスポート', 'requester_incident': '申請者とインシデント', 'name': '氏名', 'email': 'メール', 'phone': '電話', 'not_provided': '未入力', 'platform': 'プラットフォーム', 'account_handle': 'アカウント名', 'incident_date': '発生日', 'evidence_link': '証拠リンク', 'open_supplied': '提供リンクを開く', 'not_supplied': '未提供', 'intake_triage': '初期トリアージ', 'indicator_score': '指標スコア', 'advisory_only': '参考情報のみ', 'matched_indicators': '一致した指標', 'none_detected': '設定済みの指標は検出されませんでした', 'original_report': '元の報告', 'case_management': '案件管理', 'case_status': '案件ステータス', 'save_status': 'ステータスを保存', 'submitted_title': '案件を作成しました。', 'submitted_desc': '報告を記録しました。フォローアップ用にこの参照番号を保管してください。', 'receipt_notice': '参照番号は受領確認のみを示します。調査の完了や不正行為の立証を意味しません。', 'return_home': 'ホームに戻る', 'intake_confirmed': '申請を受領しました / 02', 'received_at': '受信日時', 'case_created': '案件を正常に作成しました', 'whatsapp_unavailable': 'WhatsAppは設定されていません。案件は保存されています。サイトの連絡先をご利用ください。', 'login_subtitle': '送信内容を閲覧できるのは許可されたチームメンバーのみです。'}}
merge_locale_translations(
    LANGS, ADMIN_COPY,
    {
        'pt': ('Português', 'ltr'),
        'tr': ('Türkçe', 'ltr'),
        'zh': ('简体中文', 'ltr'),
        'ja': ('日本語', 'ltr'),
    }
)

# The four admin-only locales were not part of the original marketing-site catalog.
# Give shared navigation and login/status controls real translations instead of labels
# silently falling back to English in the admin shell.
ADMIN_SHELL_COPY = {
    'pt': {'nav_home':'Início','nav_services':'Serviços','nav_about':'Sobre','nav_contact':'Contacto','privacy':'Privacidade','footer_note':'Consultoria independente, sem afiliação a plataformas sociais.','menu':'Abrir menu','loading':'A INICIAR INTERFACE SEGURA','loading_sub':'A ESTABELECER SESSÃO','login':'Acesso da equipa','username':'Nome de utilizador','password':'Palavra-passe','sign_in':'Entrar','logout':'Sair','dashboard':'Painel de casos','case':'Caso','status_label':'Estado','new':'Novo','reviewing':'Em análise','closed':'Encerrado','update':'Atualizar','no_cases':'Ainda não existem casos.','login_kicker':'ACESSO RESTRITO / EQUIPA','cat_recovery':'Acesso e recuperação da conta','cat_hacked':'Resposta a conta comprometida','cat_impersonation':'Usurpação de identidade e perfis falsos','cat_scam':'Avaliação de incidente de fraude','cat_privacy':'Privacidade e exposição de dados','cat_reputation':'Proteção da marca e reputação','cat_compliance':'Orientação sobre políticas e conformidade','cat_security':'Verificação de segurança e prevenção','cat_risk':'Resposta a riscos digitais','cat_other':'Outro pedido','platform_none':'Não especificada','platform_instagram':'Instagram','platform_facebook':'Facebook','platform_tiktok':'TikTok','platform_google':'Google','platform_x':'X','platform_linkedin':'LinkedIn','platform_other':'Outra','priority_normal':'Normal','priority_high':'Elevada','priority_critical':'Crítica — incidente ativo','invalid_credentials':'Nome de utilizador ou palavra-passe inválidos.','case_status_updated':'Estado do caso atualizado.'},
    'tr': {'nav_home':'Ana sayfa','nav_services':'Hizmetler','nav_about':'Hakkımızda','nav_contact':'İletişim','privacy':'Gizlilik','footer_note':'Bağımsız danışmanlık; sosyal platformlarla bağlantılı değildir.','menu':'Menüyü aç','loading':'GÜVENLİ ARAYÜZ BAŞLATILIYOR','loading_sub':'OTURUM OLUŞTURULUYOR','login':'Ekip girişi','username':'Kullanıcı adı','password':'Parola','sign_in':'Giriş yap','logout':'Çıkış yap','dashboard':'Dosya panosu','case':'Dosya','status_label':'Durum','new':'Yeni','reviewing':'İnceleniyor','closed':'Kapatıldı','update':'Güncelle','no_cases':'Henüz dosya yok.','login_kicker':'KISITLI ERİŞİM / EKİP','cat_recovery':'Hesap erişimi ve kurtarma','cat_hacked':'Ele geçirilmiş hesaba müdahale','cat_impersonation':'Kimliğe bürünme ve sahte profiller','cat_scam':'Dolandırıcılık olayının değerlendirilmesi','cat_privacy':'Gizlilik ve veri ifşası','cat_reputation':'Marka ve itibar koruması','cat_compliance':'Politika ve uyumluluk rehberliği','cat_security':'Güvenlik kontrolü ve önleme','cat_risk':'Dijital risk müdahalesi','cat_other':'Diğer talep','platform_none':'Belirtilmedi','platform_instagram':'Instagram','platform_facebook':'Facebook','platform_tiktok':'TikTok','platform_google':'Google','platform_x':'X','platform_linkedin':'LinkedIn','platform_other':'Diğer','priority_normal':'Normal','priority_high':'Yüksek','priority_critical':'Kritik — olay devam ediyor','invalid_credentials':'Kullanıcı adı veya parola geçersiz.','case_status_updated':'Dosya durumu güncellendi.'},
    'zh': {'nav_home':'首页','nav_services':'服务','nav_about':'关于','nav_contact':'联系','privacy':'隐私','footer_note':'独立咨询服务，与社交平台无关联。','menu':'打开菜单','loading':'正在初始化安全界面','loading_sub':'正在建立会话','login':'团队登录','username':'用户名','password':'密码','sign_in':'登录','logout':'退出','dashboard':'案件管理面板','case':'案件','status_label':'状态','new':'新建','reviewing':'审核中','closed':'已关闭','update':'更新','no_cases':'暂无案件。','login_kicker':'受限访问 / 团队','cat_recovery':'账户访问与恢复','cat_hacked':'被入侵账户应对','cat_impersonation':'身份冒用与虚假账号','cat_scam':'诈骗事件评估','cat_privacy':'隐私与数据泄露','cat_reputation':'品牌与声誉保护','cat_compliance':'政策与合规指导','cat_security':'安全检查与预防','cat_risk':'数字风险响应','cat_other':'其他请求','platform_none':'未指定','platform_instagram':'Instagram','platform_facebook':'Facebook','platform_tiktok':'TikTok','platform_google':'Google','platform_x':'X','platform_linkedin':'LinkedIn','platform_other':'其他','priority_normal':'普通','priority_high':'高','priority_critical':'紧急 — 事件仍在持续','invalid_credentials':'用户名或密码不正确。','case_status_updated':'案件状态已更新。'},
    'ja': {'nav_home':'ホーム','nav_services':'サービス','nav_about':'概要','nav_contact':'お問い合わせ','privacy':'プライバシー','footer_note':'独立したコンサルティングであり、SNSプラットフォームとは提携していません。','menu':'メニューを開く','loading':'セキュアな画面を初期化中','loading_sub':'セッションを確立中','login':'チームログイン','username':'ユーザー名','password':'パスワード','sign_in':'ログイン','logout':'ログアウト','dashboard':'案件ダッシュボード','case':'案件','status_label':'ステータス','new':'新規','reviewing':'確認中','closed':'終了','update':'更新','no_cases':'案件はまだありません。','login_kicker':'制限付きアクセス / チーム','cat_recovery':'アカウントへのアクセスと復旧','cat_hacked':'侵害されたアカウントへの対応','cat_impersonation':'なりすまし・偽プロフィール','cat_scam':'詐欺インシデントの評価','cat_privacy':'プライバシーとデータ漏えい','cat_reputation':'ブランドと評判の保護','cat_compliance':'ポリシーとコンプライアンスの案内','cat_security':'セキュリティ点検と予防','cat_risk':'デジタルリスクへの対応','cat_other':'その他の依頼','platform_none':'未指定','platform_instagram':'Instagram','platform_facebook':'Facebook','platform_tiktok':'TikTok','platform_google':'Google','platform_x':'X','platform_linkedin':'LinkedIn','platform_other':'その他','priority_normal':'通常','priority_high':'高','priority_critical':'緊急 — インシデント継続中','invalid_credentials':'ユーザー名またはパスワードが正しくありません。','case_status_updated':'案件のステータスを更新しました。'},
}
for _locale, _labels in ADMIN_SHELL_COPY.items():
    LANGS[_locale].update(_labels)

ADMIN_LOGIN_KICKER = {
    'en':'RESTRICTED ACCESS / TEAM', 'fr':'ACCÈS RÉSERVÉ / ÉQUIPE',
    'ar':'دخول مقيّد / الفريق', 'ar-tn':'دخول مقيّد / الفريق',
    'es':'ACCESO RESTRINGIDO / EQUIPO', 'de':'BESCHRÄNKTER ZUGANG / TEAM',
    'it':'ACCESSO RISERVATO / TEAM', 'pt':'ACESSO RESTRITO / EQUIPA',
    'tr':'KISITLI ERİŞİM / EKİP', 'zh':'受限访问 / 团队', 'ja':'制限付きアクセス / チーム',
}
for _locale, _label in ADMIN_LOGIN_KICKER.items():
    LANGS[_locale]['login_kicker'] = _label

# One shared label was missing from the original form dictionary, causing the raw key
# "required_note" to appear beside the first form section.
FORM_COPY['en']['required_note'] = 'Fields marked * are required.'
FORM_COPY['en']['cat_risk'] = 'Digital risk response'
FORM_COPY['fr']['required_note'] = 'Les champs marqués * sont obligatoires.'
FORM_COPY['fr']['cat_risk'] = 'Réponse aux risques numériques'
FORM_COPY['ar']['required_note'] = 'الحقول المعلّمة بنجمة * مطلوبة.'
FORM_COPY['ar']['cat_risk'] = 'الاستجابة للمخاطر الرقمية'
FORM_COPY['ar-tn']['required_note'] = 'الخانات اللي عليها * لازم تتعبّى.'
FORM_COPY['ar-tn']['cat_risk'] = 'الاستجابة للمخاطر الرقمية'
for _locale in ('en', 'fr', 'ar', 'ar-tn'):
    LANGS[_locale]['required_note'] = FORM_COPY[_locale]['required_note']
    LANGS[_locale]['cat_risk'] = FORM_COPY[_locale]['cat_risk']


TRIAGE_COPY = {'en': ['Automated intake triage — review required, not a fraud determination.', 'Priority', 'Risk indicators', 'Recommended checks: confirm ownership through official platform channels; inspect timestamps and original notifications; preserve unedited evidence; never request passwords, OTPs, recovery keys, or remote access.', 'Limitations: text heuristics can produce false positives and false negatives. A human reviewer must assess context.', 'Credential request', 'Guaranteed recovery claim', 'Off-platform payment pressure'], 'fr': ['Tri initial automatisé — une revue est nécessaire ; aucune fraude n’est établie.', 'Priorité', 'Indicateurs de risque', 'Vérifications recommandées : confirmer la propriété via les canaux officiels ; vérifier les dates et notifications ; conserver les preuves originales ; ne jamais demander de mots de passe, codes ou accès à distance.', 'Limites : les règles textuelles peuvent produire des faux positifs et négatifs. Une personne doit examiner le contexte.', 'Demande d’identifiants', 'Promesse de récupération garantie', 'Pression au paiement hors plateforme'], 'ar': ['فرز آلي أولي — يلزم التحقق البشري، ولا يمثل حكماً بالاحتيال.', 'الأولوية', 'مؤشرات المخاطر', 'التحقق الموصى به: تأكيد الملكية عبر القنوات الرسمية، ومراجعة التواريخ والإشعارات الأصلية، وحفظ الأدلة دون تعديل، وعدم طلب كلمات المرور أو الرموز أو الوصول عن بُعد.', 'القيود: قد تنتج القواعد النصية نتائج إيجابية أو سلبية خاطئة. يجب على مراجع بشري تقييم السياق.', 'طلب بيانات الدخول', 'ادعاء استعادة مضمونة', 'ضغط للدفع خارج المنصة'], 'ar-tn': ['فرز آلي أولي — يلزم تثبّت بشري، وموش حكم بالتحيّل.', 'الأولوية', 'مؤشرات المخاطر', 'التثبت المقترح: تأكيد الملكية عبر القنوات الرسمية، مراجعة التواريخ والإشعارات الأصلية، حفظ الأدلة كما هي، وعدم طلب كلمات السر أو الأكواد أو الدخول عن بعد.', 'الحدود: القواعد النصية تنجم تعطي نتائج غالطة. يلزم مراجع بشري يفهم السياق.', 'طلب معلومات الدخول', 'وعد باسترجاع مضمون', 'ضغط للدفع خارج المنصة'], 'es': ['Clasificación automática inicial: requiere revisión; no determina fraude.', 'Prioridad', 'Indicadores de riesgo', 'Comprobaciones recomendadas: confirmar la propiedad por canales oficiales, revisar fechas y avisos originales, conservar pruebas sin modificar y nunca solicitar contraseñas, códigos o acceso remoto.', 'Limitaciones: las reglas de texto pueden generar falsos positivos y negativos. Una persona debe evaluar el contexto.', 'Solicitud de credenciales', 'Promesa de recuperación garantizada', 'Presión de pago fuera de la plataforma'], 'de': ['Automatische Ersteinstufung — Prüfung erforderlich, keine Betrugsfeststellung.', 'Priorität', 'Risikohinweise', 'Empfohlene Prüfungen: Eigentum über offizielle Kanäle bestätigen, Zeitstempel und Originalmeldungen prüfen, Belege unverändert sichern und niemals Passwörter, Codes oder Fernzugriff verlangen.', 'Einschränkungen: Textregeln können falsch-positive und falsch-negative Ergebnisse liefern. Der Kontext muss menschlich geprüft werden.', 'Anfrage nach Zugangsdaten', 'Versprechen garantierter Wiederherstellung', 'Zahlungsdruck außerhalb der Plattform'], 'it': ['Valutazione automatica iniziale — richiede revisione e non accerta una frode.', 'Priorità', 'Indicatori di rischio', 'Verifiche consigliate: confermare la proprietà tramite canali ufficiali, controllare date e notifiche originali, conservare prove non modificate e non chiedere mai password, codici o accesso remoto.', 'Limiti: le regole testuali possono generare falsi positivi e negativi. Il contesto deve essere valutato da una persona.', 'Richiesta di credenziali', 'Promessa di recupero garantito', 'Pressione per pagamenti fuori piattaforma'], 'pt': ['Triagem automática inicial — requer revisão; não determina fraude.', 'Prioridade', 'Indicadores de risco', 'Verificações recomendadas: confirmar a titularidade pelos canais oficiais, rever datas e notificações originais, preservar provas sem alterações e nunca pedir palavras-passe, códigos ou acesso remoto.', 'Limitações: regras de texto podem gerar falsos positivos e negativos. Uma pessoa deve avaliar o contexto.', 'Pedido de credenciais', 'Promessa de recuperação garantida', 'Pressão para pagamento fora da plataforma'], 'tr': ['Otomatik ilk sınıflandırma — inceleme gerekir; dolandırıcılık kararı değildir.', 'Öncelik', 'Risk göstergeleri', 'Önerilen kontroller: sahipliği resmî kanallardan doğrulayın, zaman damgalarını ve özgün bildirimleri inceleyin, kanıtları değiştirmeden saklayın; parola, kod veya uzaktan erişim istemeyin.', 'Sınırlamalar: metin kuralları yanlış pozitif ve negatif sonuç verebilir. Bağlam bir kişi tarafından değerlendirilmelidir.', 'Kimlik bilgisi talebi', 'Garantili kurtarma iddiası', 'Platform dışı ödeme baskısı'], 'zh': ['自动初步分流 — 需要人工审核，不构成欺诈认定。', '优先级', '风险指标', '建议核查：通过官方渠道确认账户所有权，检查时间戳和原始通知，保存未修改的证据，绝不索要密码、验证码或远程访问。', '局限性：文本规则可能产生误报和漏报。必须由人工评估上下文。', '索取凭据', '保证恢复的承诺', '平台外付款压力'], 'ja': ['自動初期トリアージ — 要確認。詐欺の断定ではありません。', '優先度', 'リスク指標', '推奨確認事項：公式窓口で所有権を確認し、日時と元の通知を確認し、証拠を未編集で保存する。パスワード、認証コード、遠隔アクセスを求めない。', '制限事項：テキスト判定には誤検知と見逃しがあります。担当者が文脈を確認してください。', '認証情報の要求', '復旧保証の主張', 'プラットフォーム外での支払い圧力']}
for _locale, _parts in TRIAGE_COPY.items():
    LANGS[_locale].update({'triage_intro':_parts[0], 'triage_priority':_parts[1], 'triage_indicators':_parts[2], 'triage_recommendations':_parts[3], 'triage_limits':_parts[4], 'flag_credential_request':_parts[5], 'flag_guaranteed_recovery_claim':_parts[6], 'flag_off_platform_payment_pressure':_parts[7]})


# UI accessibility and dashboard interaction copy. Every supported locale has every key.
UI_COPY = {'en': {'skip_to_content': 'Skip to main content',
        'primary_navigation': 'Primary navigation',
        'language_label': 'Choose language',
        'back_to_top': 'Back to top',
        'dashboard_metrics': 'Case metrics',
        'dashboard_filter': 'Filter cases',
        'dashboard_search_placeholder': 'Search reference, requester, email or platform…',
        'dashboard_status_filter': 'Filter by status',
        'dashboard_all_statuses': 'All statuses',
        'dashboard_no_matches': 'No cases match these filters.',
        'dashboard_showing': 'Showing __visible__ of __total__ loaded cases',
        'cases_table_label': 'Recent case submissions',
        'dashboard_recent_limit': 'This view shows the 250 most recent cases. Use CSV export for the full '
                                  'dataset.',
        'copy_reference': 'Copy reference',
        'reference_copied': 'Case reference copied.',
        'copy_failed': 'Copy failed. Select the reference and copy it manually.',
        'print_report': 'Print report',
        'invalid_credentials': 'Invalid username or password.',
        'case_status_updated': 'Case status updated.',
        'submitting_request': 'Submitting request…',
        'whatsapp_consent_label': 'I agree that the information I submitted, including my contact details '
                                  'and incident description, and the generated intake report may be included '
                                  'in a prefilled WhatsApp message to YAKUZA. WhatsApp is a third-party '
                                  'service. I will review the draft and press Send myself.',
        'whatsapp_consent_required': 'Please confirm that you agree to share your submitted case details in '
                                     'a WhatsApp message.',
        'whatsapp_handoff_title': 'Your case is saved — WhatsApp is ready',
        'whatsapp_handoff_body': 'Your case has been saved in the secure dashboard. Click the button below to open WhatsApp with your submitted details and generated intake report. Review the draft and press Send yourself. WhatsApp will not open until you click the button.',
        'whatsapp_open_button': 'Open WhatsApp message',
        'whatsapp_waiting': 'WhatsApp has not been opened. Click the button above to open the prepared message. Nothing is sent until you press Send in WhatsApp.',
        'case_save_failed': 'We could not save your case. Nothing was sent to WhatsApp. Please try again '
                            'shortly.',
        'submission_slow': 'This is taking longer than expected. Keep this page open; do not submit the case '
                           'again yet.'},
 'fr': {'skip_to_content': 'Aller au contenu principal',
        'primary_navigation': 'Navigation principale',
        'language_label': 'Choisir la langue',
        'back_to_top': 'Retour en haut',
        'dashboard_metrics': 'Indicateurs des dossiers',
        'dashboard_filter': 'Filtrer les dossiers',
        'dashboard_search_placeholder': 'Rechercher référence, demandeur, e-mail ou plateforme…',
        'dashboard_status_filter': 'Filtrer par statut',
        'dashboard_all_statuses': 'Tous les statuts',
        'dashboard_no_matches': 'Aucun dossier ne correspond à ces filtres.',
        'dashboard_showing': 'Affichage de __visible__ sur __total__ dossiers chargés',
        'cases_table_label': 'Demandes récentes',
        'dashboard_recent_limit': 'Cette vue affiche les 250 dossiers les plus récents. Utilisez le CSV pour '
                                  'toutes les données.',
        'copy_reference': 'Copier la référence',
        'reference_copied': 'Référence copiée.',
        'copy_failed': 'Copie impossible. Sélectionnez puis copiez la référence manuellement.',
        'print_report': 'Imprimer le rapport',
        'invalid_credentials': 'Identifiant ou mot de passe incorrect.',
        'case_status_updated': 'Statut du dossier mis à jour.',
        'submitting_request': 'Envoi de la demande…',
        'whatsapp_consent_label': 'J’accepte que les informations saisies, y compris mes coordonnées et la '
                                  'description de l’incident, ainsi que le rapport généré, figurent dans un '
                                  'message WhatsApp prérempli destiné à YAKUZA. WhatsApp est un service '
                                  'tiers. Je vérifierai le brouillon et appuierai moi-même sur Envoyer.',
        'whatsapp_consent_required': 'Veuillez confirmer votre accord pour partager les détails du dossier '
                                     'dans un message WhatsApp.',
        'whatsapp_handoff_title': 'Votre dossier est enregistré — WhatsApp est prêt',
        'whatsapp_handoff_body': 'Votre dossier est enregistré dans le tableau de bord sécurisé. Cliquez sur le bouton ci-dessous pour ouvrir WhatsApp avec vos informations et le rapport généré. Vérifiez le brouillon puis appuyez vous-même sur Envoyer. WhatsApp ne s’ouvrira pas avant votre clic.',
        'whatsapp_open_button': 'Ouvrir le message WhatsApp',
        'whatsapp_waiting': 'WhatsApp n’a pas été ouvert. Cliquez sur le bouton ci-dessus pour ouvrir le message préparé. Rien n’est envoyé avant que vous appuyiez sur Envoyer dans WhatsApp.',
        'case_save_failed': 'Impossible d’enregistrer le dossier. Aucun message WhatsApp n’a été envoyé. '
                            'Réessayez dans un instant.',
        'submission_slow': 'Le traitement prend plus de temps que prévu. Gardez cette page ouverte et ne '
                           'renvoyez pas encore le dossier.'},
 'ar': {'skip_to_content': 'تجاوز إلى المحتوى الرئيسي',
        'primary_navigation': 'التنقل الرئيسي',
        'language_label': 'اختر اللغة',
        'back_to_top': 'العودة إلى الأعلى',
        'dashboard_metrics': 'مؤشرات الملفات',
        'dashboard_filter': 'تصفية الملفات',
        'dashboard_search_placeholder': 'ابحث بالمرجع أو مقدم الطلب أو البريد أو المنصة…',
        'dashboard_status_filter': 'التصفية حسب الحالة',
        'dashboard_all_statuses': 'كل الحالات',
        'dashboard_no_matches': 'لا توجد ملفات تطابق عوامل التصفية.',
        'dashboard_showing': 'عرض __visible__ من أصل __total__ ملف محمّل',
        'cases_table_label': 'أحدث الطلبات',
        'dashboard_recent_limit': 'تعرض هذه الصفحة أحدث 250 ملفاً. استخدم تصدير CSV للحصول على كامل '
                                  'البيانات.',
        'copy_reference': 'نسخ المرجع',
        'reference_copied': 'تم نسخ مرجع الملف.',
        'copy_failed': 'تعذر النسخ. حدّد المرجع وانسخه يدوياً.',
        'print_report': 'طباعة التقرير',
        'invalid_credentials': 'اسم المستخدم أو كلمة المرور غير صحيحة.',
        'case_status_updated': 'تم تحديث حالة الملف.',
        'submitting_request': 'جارٍ إرسال الطلب…',
        'whatsapp_consent_label': 'أوافق على تضمين المعلومات التي قدمتها، بما فيها بيانات الاتصال ووصف '
                                  'الحادثة وتقرير الفرز المُنشأ، في رسالة واتساب جاهزة إلى YAKUZA. واتساب '
                                  'خدمة تابعة لطرف ثالث. سأراجع الرسالة وأضغط على إرسال بنفسي.',
        'whatsapp_consent_required': 'يرجى تأكيد موافقتك على مشاركة تفاصيل الملف في رسالة واتساب.',
        'whatsapp_handoff_title': 'تم حفظ ملفك — واتساب جاهز',
        'whatsapp_handoff_body': 'تم حفظ ملفك في لوحة التحكم الآمنة. اضغط الزر أدناه لفتح واتساب مع المعلومات التي قدمتها والتقرير المُنشأ. راجع المسودة واضغط إرسال بنفسك. لن يفتح واتساب إلا بعد الضغط على الزر.',
        'whatsapp_open_button': 'افتح رسالة واتساب',
        'whatsapp_waiting': 'لم يتم فتح واتساب بعد. اضغط الزر أعلاه لفتح الرسالة الجاهزة. لن يتم إرسال أي شيء حتى تضغط على إرسال داخل واتساب.',
        'case_save_failed': 'تعذر حفظ ملفك. لم يتم إرسال أي رسالة إلى واتساب. يرجى المحاولة بعد قليل.',
        'submission_slow': 'يستغرق الطلب وقتاً أطول من المتوقع. اترك الصفحة مفتوحة ولا ترسل الطلب مرة أخرى '
                           'الآن.'},
 'ar-tn': {'skip_to_content': 'تعدّى للمحتوى الرئيسي',
           'primary_navigation': 'القائمة الرئيسية',
           'language_label': 'اختار اللغة',
           'back_to_top': 'ارجع للفوق',
           'dashboard_metrics': 'مؤشرات الملفات',
           'dashboard_filter': 'صفّي الملفات',
           'dashboard_search_placeholder': 'فتّش بالمرجع أو الاسم أو الإيميل أو المنصة…',
           'dashboard_status_filter': 'صفّي حسب الحالة',
           'dashboard_all_statuses': 'كل الحالات',
           'dashboard_no_matches': 'ما فما حتى ملف يطابق التصفية هاذي.',
           'dashboard_showing': 'نعرضو __visible__ من __total__ ملف ظاهر',
           'cases_table_label': 'أحدث الطلبات',
           'dashboard_recent_limit': 'الصفحة تعرض آخر 250 ملف. استعمل تصدير CSV للبيانات الكل.',
           'copy_reference': 'انسخ المرجع',
           'reference_copied': 'تم نسخ مرجع الملف.',
           'copy_failed': 'النسخ ما نجحش. حدّد المرجع وانسخو يدوياً.',
           'print_report': 'اطبع التقرير',
           'invalid_credentials': 'اسم المستخدم ولا كلمة السر موش صحيحين.',
           'case_status_updated': 'تحدّثت حالة الملف.',
           'submitting_request': 'قاعدين نبعثو في الطلب…',
           'whatsapp_consent_label': 'نوافق اللي المعلومات اللي دخلتها، بما فيها بيانات الاتصال ووصف المشكلة '
                                     'والتقرير الآلي، تتحط في رسالة واتساب جاهزة لـ YAKUZA. واتساب خدمة '
                                     'خارجية. نراجع الرسالة ونضغط على إرسال بنفسي.',
           'whatsapp_consent_required': 'أكد موافقتك على مشاركة تفاصيل الملف في رسالة واتساب.',
           'whatsapp_handoff_title': 'ملفك تسجّل — واتساب حاضر',
           'whatsapp_handoff_body': 'الملف متاعك تسجّل في لوحة التحكّم المحمية. اضغط على الزر اللي لتحت باش تحلّ واتساب وفيه المعلومات والتقرير. راجع المسودة واضغط إرسال بنفسك. واتساب ما يتحلّ كان كي تضغط على الزر.',
           'whatsapp_open_button': 'افتح رسالة واتساب',
           'whatsapp_waiting': 'واتساب ما تحلّش توّا. اضغط على الزر اللي فوق باش تحلّ الرسالة الجاهزة. ما يتبعث حتى شي كان كي تضغط إرسال في واتساب.',
           'case_save_failed': 'ما نجّمش نحفظو الملف. ما تبعث حتى شي لواتساب. عاود جرّب بعد شوية.',
           'submission_slow': 'الطلب طول أكثر من العادة. خلّي الصفحة محلولة وما تعاودش تبعث الملف توّا.'},
 'es': {'skip_to_content': 'Saltar al contenido principal',
        'primary_navigation': 'Navegación principal',
        'language_label': 'Elegir idioma',
        'back_to_top': 'Volver arriba',
        'dashboard_metrics': 'Métricas de casos',
        'dashboard_filter': 'Filtrar casos',
        'dashboard_search_placeholder': 'Buscar referencia, solicitante, correo o plataforma…',
        'dashboard_status_filter': 'Filtrar por estado',
        'dashboard_all_statuses': 'Todos los estados',
        'dashboard_no_matches': 'Ningún caso coincide con estos filtros.',
        'dashboard_showing': 'Mostrando __visible__ de __total__ casos cargados',
        'cases_table_label': 'Solicitudes recientes',
        'dashboard_recent_limit': 'Esta vista muestra los 250 casos más recientes. Usa la exportación CSV '
                                  'para todos los datos.',
        'copy_reference': 'Copiar referencia',
        'reference_copied': 'Referencia del caso copiada.',
        'copy_failed': 'No se pudo copiar. Selecciona y copia la referencia manualmente.',
        'print_report': 'Imprimir informe',
        'invalid_credentials': 'Usuario o contraseña incorrectos.',
        'case_status_updated': 'Estado del caso actualizado.',
        'submitting_request': 'Enviando la solicitud…',
        'whatsapp_consent_label': 'Acepto que la información que he enviado, incluidos mis datos de contacto '
                                  'y la descripción del incidente, y el informe generado se incluyan en un '
                                  'mensaje de WhatsApp precompletado para YAKUZA. WhatsApp es un servicio de '
                                  'terceros. Revisaré el borrador y pulsaré Enviar personalmente.',
        'whatsapp_consent_required': 'Confirma que aceptas compartir los datos del caso en un mensaje de '
                                     'WhatsApp.',
        'whatsapp_handoff_title': 'Tu caso está guardado — WhatsApp está listo',
        'whatsapp_handoff_body': 'Tu caso se ha guardado en el panel seguro. Pulsa el botón de abajo para abrir WhatsApp con tus datos y el informe generado. Revisa el borrador y pulsa Enviar tú mismo. WhatsApp no se abrirá hasta que pulses el botón.',
        'whatsapp_open_button': 'Abrir mensaje de WhatsApp',
        'whatsapp_waiting': 'WhatsApp todavía no se ha abierto. Pulsa el botón de arriba para abrir el mensaje preparado. No se enviará nada hasta que pulses Enviar en WhatsApp.',
        'case_save_failed': 'No se pudo guardar el caso. No se envió nada a WhatsApp. Inténtalo de nuevo.',
        'submission_slow': 'Esto está tardando más de lo esperado. Mantén esta página abierta y no vuelvas a '
                           'enviar el caso todavía.'},
 'de': {'skip_to_content': 'Zum Hauptinhalt springen',
        'primary_navigation': 'Hauptnavigation',
        'language_label': 'Sprache auswählen',
        'back_to_top': 'Nach oben',
        'dashboard_metrics': 'Fallkennzahlen',
        'dashboard_filter': 'Fälle filtern',
        'dashboard_search_placeholder': 'Referenz, Anfragende, E-Mail oder Plattform suchen…',
        'dashboard_status_filter': 'Nach Status filtern',
        'dashboard_all_statuses': 'Alle Status',
        'dashboard_no_matches': 'Keine Fälle entsprechen diesen Filtern.',
        'dashboard_showing': '__visible__ von __total__ geladenen Fällen angezeigt',
        'cases_table_label': 'Neueste Fallanfragen',
        'dashboard_recent_limit': 'Diese Ansicht zeigt die 250 neuesten Fälle. Für alle Daten den CSV-Export '
                                  'verwenden.',
        'copy_reference': 'Referenz kopieren',
        'reference_copied': 'Fallreferenz kopiert.',
        'copy_failed': 'Kopieren fehlgeschlagen. Referenz markieren und manuell kopieren.',
        'print_report': 'Bericht drucken',
        'invalid_credentials': 'Benutzername oder Passwort ungültig.',
        'case_status_updated': 'Fallstatus aktualisiert.',
        'submitting_request': 'Anfrage wird gesendet…',
        'whatsapp_consent_label': 'Ich stimme zu, dass meine Angaben einschließlich Kontaktdaten und '
                                  'Vorfallsbeschreibung sowie der erstellte Intake-Bericht in eine '
                                  'vorausgefüllte WhatsApp-Nachricht an YAKUZA aufgenommen werden. WhatsApp '
                                  'ist ein Drittanbieterdienst. Ich prüfe den Entwurf und drücke selbst auf '
                                  'Senden.',
        'whatsapp_consent_required': 'Bitte bestätige, dass du die Falldaten in einer WhatsApp-Nachricht '
                                     'teilen möchtest.',
        'whatsapp_handoff_title': 'Dein Fall ist gespeichert — WhatsApp ist bereit',
        'whatsapp_handoff_body': 'Dein Fall wurde im geschützten Dashboard gespeichert. Klicke auf die Schaltfläche unten, um WhatsApp mit deinen Angaben und dem erstellten Bericht zu öffnen. Prüfe den Entwurf und drücke selbst auf Senden. WhatsApp wird erst nach deinem Klick geöffnet.',
        'whatsapp_open_button': 'WhatsApp-Nachricht öffnen',
        'whatsapp_waiting': 'WhatsApp wurde noch nicht geöffnet. Klicke oben auf die Schaltfläche, um die vorbereitete Nachricht zu öffnen. Gesendet wird erst, wenn du in WhatsApp auf Senden drückst.',
        'case_save_failed': 'Der Fall konnte nicht gespeichert werden. Es wurde nichts an WhatsApp gesendet. '
                            'Bitte versuche es erneut.',
        'submission_slow': 'Dies dauert länger als erwartet. Lass diese Seite geöffnet und sende den Fall '
                           'vorerst nicht erneut.'},
 'it': {'skip_to_content': 'Vai al contenuto principale',
        'primary_navigation': 'Navigazione principale',
        'language_label': 'Scegli la lingua',
        'back_to_top': 'Torna su',
        'dashboard_metrics': 'Metriche dei casi',
        'dashboard_filter': 'Filtra i casi',
        'dashboard_search_placeholder': 'Cerca riferimento, richiedente, e-mail o piattaforma…',
        'dashboard_status_filter': 'Filtra per stato',
        'dashboard_all_statuses': 'Tutti gli stati',
        'dashboard_no_matches': 'Nessun caso corrisponde a questi filtri.',
        'dashboard_showing': 'Visualizzati __visible__ di __total__ casi caricati',
        'cases_table_label': 'Richieste recenti',
        'dashboard_recent_limit': 'Questa vista mostra i 250 casi più recenti. Usa l’esportazione CSV per '
                                  'tutti i dati.',
        'copy_reference': 'Copia riferimento',
        'reference_copied': 'Riferimento del caso copiato.',
        'copy_failed': 'Copia non riuscita. Seleziona e copia il riferimento manualmente.',
        'print_report': 'Stampa rapporto',
        'invalid_credentials': 'Nome utente o password non validi.',
        'case_status_updated': 'Stato del caso aggiornato.',
        'submitting_request': 'Invio della richiesta…',
        'whatsapp_consent_label': 'Acconsento a includere le informazioni inviate, compresi i dati di '
                                  'contatto e la descrizione dell’incidente, insieme al rapporto generato, '
                                  'in un messaggio WhatsApp precompilato per YAKUZA. WhatsApp è un servizio '
                                  'di terze parti. Controllerò il testo e premerò personalmente Invia.',
        'whatsapp_consent_required': 'Conferma di accettare la condivisione dei dettagli del caso tramite un '
                                     'messaggio WhatsApp.',
        'whatsapp_handoff_title': 'Il caso è salvato — WhatsApp è pronto',
        'whatsapp_handoff_body': 'Il caso è stato salvato nella dashboard protetta. Fai clic sul pulsante qui sotto per aprire WhatsApp con i dati inviati e il rapporto generato. Controlla la bozza e premi tu stesso Invia. WhatsApp non si aprirà finché non farai clic sul pulsante.',
        'whatsapp_open_button': 'Apri il messaggio WhatsApp',
        'whatsapp_waiting': 'WhatsApp non è ancora stato aperto. Fai clic sul pulsante qui sopra per aprire il messaggio preparato. Non verrà inviato nulla finché non premi Invia in WhatsApp.',
        'case_save_failed': 'Impossibile salvare il caso. Non è stato inviato nulla a WhatsApp. Riprova tra '
                            'poco.',
        'submission_slow': 'L’operazione sta richiedendo più tempo del previsto. Lascia aperta questa pagina '
                           'e non inviare di nuovo il caso per ora.'},
 'pt': {'skip_to_content': 'Ir para o conteúdo principal',
        'primary_navigation': 'Navegação principal',
        'language_label': 'Escolher idioma',
        'back_to_top': 'Voltar ao topo',
        'dashboard_metrics': 'Indicadores dos casos',
        'dashboard_filter': 'Filtrar casos',
        'dashboard_search_placeholder': 'Pesquisar referência, solicitante, e-mail ou plataforma…',
        'dashboard_status_filter': 'Filtrar por estado',
        'dashboard_all_statuses': 'Todos os estados',
        'dashboard_no_matches': 'Nenhum caso corresponde a estes filtros.',
        'dashboard_showing': 'A mostrar __visible__ de __total__ casos carregados',
        'cases_table_label': 'Pedidos recentes',
        'dashboard_recent_limit': 'Esta vista mostra os 250 casos mais recentes. Use a exportação CSV para '
                                  'todos os dados.',
        'copy_reference': 'Copiar referência',
        'reference_copied': 'Referência do caso copiada.',
        'copy_failed': 'Não foi possível copiar. Selecione e copie a referência manualmente.',
        'print_report': 'Imprimir relatório',
        'invalid_credentials': 'Nome de utilizador ou palavra-passe inválidos.',
        'case_status_updated': 'Estado do caso atualizado.',
        'submitting_request': 'A enviar o pedido…',
        'whatsapp_consent_label': 'Concordo que as informações enviadas, incluindo os meus contactos e a '
                                  'descrição do incidente, bem como o relatório gerado, sejam incluídos numa '
                                  'mensagem WhatsApp pré-preenchida para a YAKUZA. O WhatsApp é um serviço '
                                  'de terceiros. Vou rever a mensagem e carregar pessoalmente em Enviar.',
        'whatsapp_consent_required': 'Confirme que concorda em partilhar os detalhes do caso numa mensagem '
                                     'WhatsApp.',
        'whatsapp_handoff_title': 'O seu caso foi guardado — WhatsApp pronto',
        'whatsapp_handoff_body': 'O seu caso foi guardado no painel protegido. Clique no botão abaixo para abrir o WhatsApp com os dados enviados e o relatório gerado. Reveja o rascunho e carregue pessoalmente em Enviar. O WhatsApp só será aberto quando clicar no botão.',
        'whatsapp_open_button': 'Abrir mensagem do WhatsApp',
        'whatsapp_waiting': 'O WhatsApp ainda não foi aberto. Clique no botão acima para abrir a mensagem preparada. Nada será enviado até carregar em Enviar no WhatsApp.',
        'case_save_failed': 'Não foi possível guardar o caso. Nada foi enviado para o WhatsApp. Tente '
                            'novamente.',
        'submission_slow': 'Isto está a demorar mais do que o esperado. Mantenha esta página aberta e não '
                           'envie o caso novamente ainda.'},
 'tr': {'skip_to_content': 'Ana içeriğe geç',
        'primary_navigation': 'Ana gezinme',
        'language_label': 'Dil seçin',
        'back_to_top': 'Başa dön',
        'dashboard_metrics': 'Dosya ölçümleri',
        'dashboard_filter': 'Dosyaları filtrele',
        'dashboard_search_placeholder': 'Referans, başvuran, e-posta veya platform ara…',
        'dashboard_status_filter': 'Duruma göre filtrele',
        'dashboard_all_statuses': 'Tüm durumlar',
        'dashboard_no_matches': 'Bu filtrelerle eşleşen dosya yok.',
        'dashboard_showing': 'Yüklenen __total__ dosyanın __visible__ tanesi gösteriliyor',
        'cases_table_label': 'Son dosya başvuruları',
        'dashboard_recent_limit': 'Bu görünüm en son 250 dosyayı gösterir. Tüm veriler için CSV dışa '
                                  'aktarımını kullanın.',
        'copy_reference': 'Referansı kopyala',
        'reference_copied': 'Dosya referansı kopyalandı.',
        'copy_failed': 'Kopyalama başarısız. Referansı seçip elle kopyalayın.',
        'print_report': 'Raporu yazdır',
        'invalid_credentials': 'Kullanıcı adı veya parola geçersiz.',
        'case_status_updated': 'Dosya durumu güncellendi.',
        'submitting_request': 'Talep gönderiliyor…',
        'whatsapp_consent_label': 'İletişim bilgilerim ve olay açıklamam dâhil gönderdiğim bilgilerin ve '
                                  'oluşturulan başvuru raporunun YAKUZA’ya gönderilmek üzere önceden '
                                  'doldurulmuş bir WhatsApp mesajına eklenmesini kabul ediyorum. WhatsApp '
                                  'üçüncü taraf bir hizmettir. Mesajı inceleyip Gönder’e kendim basacağım.',
        'whatsapp_consent_required': 'Dosya bilgilerinin WhatsApp mesajıyla paylaşılmasına izin verdiğinizi '
                                     'onaylayın.',
        'whatsapp_handoff_title': 'Dosyanız kaydedildi — WhatsApp hazır',
        'whatsapp_handoff_body': 'Dosyanız güvenli panoya kaydedildi. Gönderdiğiniz bilgiler ve oluşturulan raporla WhatsApp’ı açmak için aşağıdaki düğmeye tıklayın. Taslağı inceleyin ve Gönder’e kendiniz basın. Düğmeye tıklayana kadar WhatsApp açılmaz.',
        'whatsapp_open_button': 'WhatsApp mesajını aç',
        'whatsapp_waiting': 'WhatsApp henüz açılmadı. Hazırlanan mesajı açmak için yukarıdaki düğmeye tıklayın. WhatsApp’ta Gönder’e basana kadar hiçbir şey gönderilmez.',
        'case_save_failed': 'Dosya kaydedilemedi. WhatsApp’a hiçbir mesaj gönderilmedi. Lütfen tekrar '
                            'deneyin.',
        'submission_slow': 'İşlem beklenenden uzun sürüyor. Bu sayfayı açık tutun ve şimdilik dosyayı tekrar '
                           'göndermeyin.'},
 'zh': {'skip_to_content': '跳转到主要内容',
        'primary_navigation': '主导航',
        'language_label': '选择语言',
        'back_to_top': '返回顶部',
        'dashboard_metrics': '案件指标',
        'dashboard_filter': '筛选案件',
        'dashboard_search_placeholder': '搜索编号、提交人、邮箱或平台…',
        'dashboard_status_filter': '按状态筛选',
        'dashboard_all_statuses': '所有状态',
        'dashboard_no_matches': '没有符合这些筛选条件的案件。',
        'dashboard_showing': '显示已加载 __total__ 个案件中的 __visible__ 个',
        'cases_table_label': '最近提交的案件',
        'dashboard_recent_limit': '此视图显示最近的 250 个案件。完整数据请使用 CSV 导出。',
        'copy_reference': '复制编号',
        'reference_copied': '案件编号已复制。',
        'copy_failed': '复制失败。请手动选择并复制编号。',
        'print_report': '打印报告',
        'invalid_credentials': '用户名或密码不正确。',
        'case_status_updated': '案件状态已更新。',
        'submitting_request': '正在提交请求…',
        'whatsapp_consent_label': '我同意将我提交的信息（包括联系方式和事件描述）以及生成的受理报告放入发送给 YAKUZA 的预填 WhatsApp 消息中。WhatsApp '
                                  '是第三方服务。我会自行检查草稿并点击发送。',
        'whatsapp_consent_required': '请确认您同意通过 WhatsApp 消息分享案件详情。',
        'whatsapp_handoff_title': '案件已保存 — WhatsApp 已准备就绪',
        'whatsapp_handoff_body': '您的案件已保存到安全管理面板。点击下方按钮，使用您提交的信息和生成的报告打开 WhatsApp。请检查草稿并由您本人点击发送。只有点击此按钮后才会打开 WhatsApp。',
        'whatsapp_open_button': '打开 WhatsApp 消息',
        'whatsapp_waiting': 'WhatsApp 尚未打开。点击上方按钮以打开已准备好的消息。只有您在 WhatsApp 中点击发送后，消息才会发送。',
        'case_save_failed': '无法保存案件。没有向 WhatsApp 发送任何消息。请稍后重试。',
        'submission_slow': '处理时间超出预期。请保持此页面打开，暂时不要重复提交案件。'},
 'ja': {'skip_to_content': 'メインコンテンツへ移動',
        'primary_navigation': 'メインナビゲーション',
        'language_label': '言語を選択',
        'back_to_top': 'ページ上部へ',
        'dashboard_metrics': '案件指標',
        'dashboard_filter': '案件を絞り込む',
        'dashboard_search_placeholder': '参照番号、申請者、メール、プラットフォームを検索…',
        'dashboard_status_filter': 'ステータスで絞り込む',
        'dashboard_all_statuses': 'すべてのステータス',
        'dashboard_no_matches': '条件に一致する案件はありません。',
        'dashboard_showing': '読み込み済み __total__ 件中 __visible__ 件を表示',
        'cases_table_label': '最近の案件一覧',
        'dashboard_recent_limit': 'この画面には直近250件が表示されます。全データはCSVでエクスポートしてください。',
        'copy_reference': '参照番号をコピー',
        'reference_copied': '案件の参照番号をコピーしました。',
        'copy_failed': 'コピーできませんでした。参照番号を選択して手動でコピーしてください。',
        'print_report': 'レポートを印刷',
        'invalid_credentials': 'ユーザー名またはパスワードが正しくありません。',
        'case_status_updated': '案件のステータスを更新しました。',
        'submitting_request': 'リクエストを送信中…',
        'whatsapp_consent_label': '連絡先とインシデントの説明を含む送信情報、および作成された受付レポートを、YAKUZA 宛ての事前入力済み WhatsApp '
                                  'メッセージに含めることに同意します。WhatsApp は第三者サービスです。内容を確認し、自分で送信ボタンを押します。',
        'whatsapp_consent_required': '案件の詳細を WhatsApp メッセージで共有することへの同意を確認してください。',
        'whatsapp_handoff_title': '案件を保存しました — WhatsApp の準備ができました',
        'whatsapp_handoff_body': '案件は保護された管理画面に保存されました。下のボタンをクリックすると、入力内容と生成されたレポートを含む WhatsApp が開きます。下書きを確認し、ご自身で送信を押してください。ボタンをクリックするまで WhatsApp は開きません。',
        'whatsapp_open_button': 'WhatsApp メッセージを開く',
        'whatsapp_waiting': 'WhatsApp はまだ開いていません。上のボタンをクリックして準備済みのメッセージを開いてください。WhatsApp で送信を押すまで何も送信されません。',
        'case_save_failed': '案件を保存できませんでした。WhatsApp へのメッセージ送信は行われていません。しばらくしてから再試行してください。',
        'submission_slow': '処理に通常より時間がかかっています。このページを開いたままにし、まだ案件を再送信しないでください。'}}
for _locale, _copy in UI_COPY.items():
    LANGS[_locale].update(_copy)

# Remove labels from the former one-page / arithmetic-check intake UI.
for _locale_catalog in LANGS.values():
    for _obsolete_key in ('preferred_label', 'private_title', 'private_desc', 'whatsapp_title', 'whatsapp_desc', 'human_label', 'human_hint', 'submit_case'):
        _locale_catalog.pop(_obsolete_key, None)


# Server-rendered intake errors; no client-side challenge/retry loop.
INTAKE_ERROR_COPY = {
    'en': {'intake_form_error':'Please check the highlighted fields and try again.', 'intake_csrf_error':'Your form session expired. Your entries have been kept. Please press Create secure case again.'},
    'fr': {'intake_form_error':'Vérifiez les champs signalés puis réessayez.', 'intake_csrf_error':'Votre session a expiré. Vos réponses ont été conservées. Cliquez à nouveau sur Créer le dossier sécurisé.'},
    'ar': {'intake_form_error':'يرجى مراجعة الحقول المحددة ثم المحاولة مجدداً.', 'intake_csrf_error':'انتهت جلسة النموذج وتم الاحتفاظ ببياناتك. اضغط إنشاء الملف الآمن مرة أخرى.'},
    'ar-tn': {'intake_form_error':'راجع الخانات المعلّمة وعاود المحاولة.', 'intake_csrf_error':'وفات جلسة الفورم أما معلوماتك بقات محفوظة. اضغط سجّل الملف الآمن من جديد.'},
    'es': {'intake_form_error':'Revisa los campos señalados y vuelve a intentarlo.', 'intake_csrf_error':'La sesión del formulario caducó. Conservamos tus datos. Pulsa de nuevo Crear caso seguro.'},
    'de': {'intake_form_error':'Bitte prüfe die markierten Felder und versuche es erneut.', 'intake_csrf_error':'Deine Formularsitzung ist abgelaufen. Deine Eingaben bleiben erhalten. Klicke erneut auf Sicheren Fall erstellen.'},
    'it': {'intake_form_error':'Controlla i campi evidenziati e riprova.', 'intake_csrf_error':'La sessione del modulo è scaduta. I tuoi dati sono stati conservati. Premi di nuovo Crea caso sicuro.'},
    'pt': {'intake_form_error':'Verifique os campos assinalados e tente novamente.', 'intake_csrf_error':'A sessão do formulário expirou. Os seus dados foram mantidos. Clique novamente em Criar caso seguro.'},
    'tr': {'intake_form_error':'Lütfen işaretli alanları kontrol edip tekrar deneyin.', 'intake_csrf_error':'Form oturumunuzun süresi doldu. Bilgileriniz korundu. Güvenli dosya oluştur düğmesine tekrar basın.'},
    'zh': {'intake_form_error':'请检查标记的字段后重试。', 'intake_csrf_error':'表单会话已过期，您填写的信息已保留。请再次点击创建安全案件。'},
    'ja': {'intake_form_error':'強調表示された項目を確認して再試行してください。', 'intake_csrf_error':'フォームの有効期限が切れました。入力内容は保持されています。もう一度「安全なケースを作成」を押してください。'},
}
for _locale, _copy in INTAKE_ERROR_COPY.items():
    LANGS[_locale].update(_copy)

INTAKE_RATE_LIMIT_COPY = {'en': {'intake_rate_limited': 'Too many submissions from this connection. Please wait before trying again.'}, 'fr': {'intake_rate_limited': 'Trop de demandes depuis cette connexion. Veuillez patienter avant de réessayer.'}, 'ar': {'intake_rate_limited': 'تم إرسال طلبات كثيرة من هذا الاتصال. يرجى الانتظار قبل إعادة المحاولة.'}, 'ar-tn': {'intake_rate_limited': 'بعثت برشة طلبات من نفس الاتصال. استنّى شوية وبعد عاود.'}, 'es': {'intake_rate_limited': 'Demasiados envíos desde esta conexión. Espera antes de volver a intentarlo.'}, 'de': {'intake_rate_limited': 'Zu viele Anfragen von dieser Verbindung. Bitte warte, bevor du es erneut versuchst.'}, 'it': {'intake_rate_limited': 'Troppe richieste da questa connessione. Attendi prima di riprovare.'}, 'pt': {'intake_rate_limited': 'Demasiados pedidos desta ligação. Aguarde antes de tentar novamente.'}, 'tr': {'intake_rate_limited': 'Bu bağlantıdan çok fazla gönderim yapıldı. Tekrar denemeden önce bekleyin.'}, 'zh': {'intake_rate_limited': '此连接提交次数过多。请稍后再试。'}, 'ja': {'intake_rate_limited': 'この接続からの送信が多すぎます。時間をおいて再試行してください。'}}
for _locale, _copy in INTAKE_RATE_LIMIT_COPY.items():
    LANGS[_locale].update(_copy)

class InquiryForm(FlaskForm):
    name=StringField(validators=[DataRequired(),Length(min=2,max=100)])
    email=EmailField(validators=[DataRequired(),Email(),Length(max=180)])
    topic=SelectField(choices=[('recovery','Account recovery'),('hacked','Compromised account'),('impersonation','Impersonation / fake profile'),('scam','Scam incident review'),('privacy','Privacy / data exposure'),('reputation','Brand / reputation protection'),('compliance','Compliance advisory'),('security','Security check-up'),('risk','Digital risk response'),('other','Other')], validators=[DataRequired()])
    message=TextAreaField(validators=[DataRequired(),Length(min=25,max=3000)])
    incident_date=StringField(validators=[Optional(),Length(max=30)])
    account_handle=StringField(validators=[Optional(),Length(max=120)])
    evidence_url=StringField(validators=[Optional(),Length(max=500)])
    urgency=SelectField(choices=[('normal','Normal'),('high','High'),('critical','Critical')],validators=[DataRequired()])
    phone=StringField(validators=[Optional(),Length(max=40)])
    platform=SelectField(choices=[('not-specified','Not specified'),('instagram','Instagram'),('facebook','Facebook'),('tiktok','TikTok'),('google','Google'),('x','X'),('linkedin','LinkedIn'),('other','Other')], validators=[DataRequired()])
    website=StringField(validators=[Optional(),Length(max=0)])
    authorization=StringField(validators=[DataRequired(),Length(max=3)])
    whatsapp_consent=StringField(validators=[DataRequired(),Length(max=3)])
    submit=SubmitField()
class LoginForm(FlaskForm):
    username=StringField(validators=[DataRequired(),Length(max=80)])
    password=PasswordField(validators=[DataRequired(),Length(max=200)])

class Inquiry(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(180),nullable=False,index=True)
    topic=db.Column(db.String(40),nullable=False)
    message=db.Column(db.Text,nullable=False)
    status=db.Column(db.String(20),nullable=False,default='new')
    created_at=db.Column(db.DateTime,nullable=False,default=lambda:datetime.now(timezone.utc))
    case_ref=db.Column(db.String(32),unique=True,index=True)
    platform=db.Column(db.String(40),default='not-specified')
    phone=db.Column(db.String(40),default='')
    incident_date=db.Column(db.String(30),default='')
    account_handle=db.Column(db.String(120),default='')
    evidence_url=db.Column(db.String(500),default='')
    urgency=db.Column(db.String(20),default='normal')
    risk_score=db.Column(db.Integer,default=0)
    risk_flags=db.Column(db.Text,default='')
    triage_report=db.Column(db.Text,default='')
    contact_method=db.Column(db.String(20),default='support')
class AdminUser(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password_hash=db.Column(db.String(255),nullable=False)

_case_handoff_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='yakuza-whatsapp-case-handoff-v1')


def issue_case_handoff_token(case_ref):
    return _case_handoff_serializer.dumps({'ref': case_ref})


def tr(key): return LANGS.get(session.get('lang','en'),LANGS['en']).get(key,LANGS['en'].get(key,key))
@app.context_processor
def inject():
    lang=session.get('lang','en'); return {'t':tr,'lang':lang,'languages':LANGS,'direction':LANGS.get(lang,LANGS['en'])['dir']}
@app.before_request
def language_and_security():
    # Correlate each request without logging submitted personal information or signed URL tokens.
    g.support_reference = uuid.uuid4().hex[:12].upper()
    g.request_started = perf_counter()
    if request.path == '/contact' and request.method == 'POST':
        app.logger.info('intake_request_received support_ref=%s content_length=%s', g.support_reference, request.content_length)
    if request.method == 'GET' and request.args.get('lang') in LANGS:
        session['lang']=request.args['lang']
        return redirect(request.path)
@app.after_request
def security_headers(resp):
    if request.path == '/contact' or request.path.startswith('/case/ready/'):
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Referrer-Policy'] = 'no-referrer'
        if request.path.startswith('/case/ready/'):
            resp.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
    if request.path == ADMIN_URL_PREFIX or request.path.startswith(ADMIN_URL_PREFIX + '/'):
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet'
    resp.headers['X-Content-Type-Options']='nosniff'; resp.headers['X-Frame-Options']='DENY'; resp.headers.setdefault('Referrer-Policy','strict-origin-when-cross-origin'); resp.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    resp.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    if app.config['SESSION_COOKIE_SECURE']: resp.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    if request.path == '/contact' and request.method == 'POST':
        elapsed = int((perf_counter() - getattr(g, 'request_started', perf_counter())) * 1000)
        app.logger.info('intake_request_completed support_ref=%s status=%s elapsed_ms=%s', getattr(g, 'support_reference', 'unknown'), resp.status_code, elapsed)
    return resp
@app.get('/')
def home(): return render_template('index.html')
@app.get('/services')
def services(): return render_template('services.html')
@app.get('/about')
def about(): return render_template('about.html')
@app.route('/contact', methods=['GET', 'POST'])
@limiter.limit(os.environ.get('INTAKE_RATE_LIMIT', '30 per hour'), methods=['POST'])
def contact():
    """Simple two-page intake: save the case, then show one WhatsApp button."""
    form = InquiryForm()

    if request.method == 'GET':
        return render_template('contact.html', form=form)

    # Flask-WTF validates the ordinary session CSRF token. No custom per-form
    # challenge, AJAX request, signed intake token, or retry loop is involved.
    if not form.validate_on_submit():
        flash(tr('intake_form_error'), 'error')
        return render_template('contact.html', form=form), 400

    if form.website.data:
        abort(400)
    if form.authorization.data != 'yes' or form.whatsapp_consent.data != 'yes':
        flash(tr('whatsapp_consent_required'), 'error')
        return render_template('contact.html', form=form), 400

    whatsapp_number = normalize_whatsapp_number(os.environ.get('WHATSAPP_NUMBER', '4917642484892'))
    if not whatsapp_number:
        app.logger.error('case_intake_rejected reason=whatsapp_not_configured')
        flash(tr('whatsapp_configuration_error'), 'error')
        return render_template('contact.html', form=form), 503

    if form.evidence_url.data:
        from urllib.parse import urlsplit
        evidence = form.evidence_url.data.strip()
        parsed = urlsplit(evidence)
        if parsed.scheme.lower() != 'https' or not parsed.netloc or parsed.username or parsed.password:
            form.evidence_url.errors.append('Enter a valid HTTPS evidence link.')
            flash(tr('intake_form_error'), 'error')
            return render_template('contact.html', form=form), 400

    message = form.message.data.strip()
    patterns = [
        ('credential_request', r'password|one.time code|otp|2fa code|recovery code'),
        ('guaranteed_recovery_claim', r'guaranteed recovery|100% recovery|instant recovery'),
        ('off_platform_payment_pressure', r'pay.*crypto|gift card|wire transfer|urgent payment'),
    ]
    flags = [label for label, pattern in patterns if re.search(pattern, message, re.I)]
    score = min(90, len(flags) * 25 + (20 if form.urgency.data == 'critical' else 10 if form.urgency.data == 'high' else 0))
    report = (
        'Automated intake triage — review required, not a fraud determination.\n'
        f'Priority: {form.urgency.data.upper()}\n'
        f"Risk indicators: {', '.join(flags) if flags else 'No configured text indicators detected'}\n"
        'Recommended checks: confirm account ownership through official platform channels; inspect timestamps and original notifications; preserve unedited evidence; never request passwords, OTPs, recovery keys, or remote access.\n'
        'Limitations: text heuristics can produce false positives and false negatives. A human reviewer must assess context.'
    )

    # Generate the reference on the server. The database unique constraint
    # remains the final guard against an astronomically unlikely collision.
    for attempt in range(3):
        case_ref = 'YKZ-' + datetime.now(timezone.utc).strftime('%y%m%d') + '-' + secrets.token_hex(6).upper()
        item = Inquiry(
            case_ref=case_ref,
            name=(form.name.data or '').strip(),
            email=(form.email.data or '').strip().lower(),
            topic=form.topic.data,
            message=message,
            platform=form.platform.data,
            phone=(form.phone.data or '').strip(),
            incident_date=(form.incident_date.data or '').strip(),
            account_handle=(form.account_handle.data or '').strip(),
            evidence_url=(form.evidence_url.data or '').strip(),
            urgency=form.urgency.data,
            risk_score=score,
            risk_flags=', '.join(flags),
            triage_report=report,
            contact_method='whatsapp',
            created_at=datetime.now(timezone.utc),
        )
        try:
            # Validate the WhatsApp draft and sign the next-page reference
            # before committing, so only the database commit remains before redirect.
            if not build_case_whatsapp_url(whatsapp_number, item):
                flash(tr('whatsapp_configuration_error'), 'error')
                return render_template('contact.html', form=form), 503
            handoff_token = issue_case_handoff_token(case_ref)
            db.session.add(item)
            db.session.commit()
            app.logger.info('case_intake_saved case_ref=%s', case_ref)
            return redirect(url_for('case_ready', token=handoff_token), code=303)
        except IntegrityError:
            db.session.rollback()
            if attempt < 2:
                continue
            app.logger.exception('case_intake_failed stage=unique_reference')
        except Exception:
            db.session.rollback()
            app.logger.exception('case_intake_failed stage=save')
            break

    flash(tr('case_save_failed'), 'error')
    return render_template('contact.html', form=form), 503


@app.get('/case/ready/<token>')
def case_ready(token):
    """Second step: show the saved case and one explicit WhatsApp hand-off button."""
    try:
        payload = _case_handoff_serializer.loads(token, max_age=24 * 60 * 60)
    except BadSignature:
        abort(404)
    case_ref = payload.get('ref') if isinstance(payload, dict) else None
    if not isinstance(case_ref, str) or not re.fullmatch(r'YKZ-[0-9]{6}-[A-F0-9]{12}', case_ref):
        abort(404)
    item = Inquiry.query.filter_by(case_ref=case_ref).first_or_404()
    whatsapp_url = build_case_whatsapp_url(os.environ.get('WHATSAPP_NUMBER', '4917642484892'), item)
    if not whatsapp_url:
        abort(503)
    return render_template('case_ready.html', item=item, whatsapp_url=whatsapp_url)


@app.errorhandler(429)
def handle_rate_limit(error):
    flash(tr('intake_rate_limited'), 'error')
    form = InquiryForm(formdata=request.form if request.method == 'POST' else None)
    return render_template('contact.html', form=form), 429


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    if request.path != '/contact':
        flash('Your security session expired. Please sign in and try again.', 'error')
        if request.endpoint == 'admin_login':
            return render_template('admin_login.html', form=LoginForm()), 400
        return render_template('index.html'), 400

    # Preserve submitted fields, but NEVER echo the rejected CSRF token back
    # into the refreshed form. Doing so creates an endless expired-token loop:
    # every retry submits the same token and fails again.
    session.pop('csrf_token', None)
    formdata = request.form.copy() if request.method == 'POST' else None
    if formdata is not None:
        formdata.pop('csrf_token', None)
    form = InquiryForm(formdata=formdata)
    flash(tr('intake_csrf_error'), 'error')
    response = app.make_response(render_template('contact.html', form=form))
    response.status_code = 400
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    # Do not convert expected 4xx/redirect HTTP exceptions into 500 responses.
    if isinstance(error, HTTPException):
        return error
    support_reference = getattr(g, 'support_reference', uuid.uuid4().hex[:12].upper())
    # Full traceback goes to Render logs; no request body or user-submitted fields are logged.
    app.logger.error(
        'unhandled_request_failure support_ref=%s method=%s endpoint=%s',
        support_reference, request.method, request.endpoint or 'unmatched',
        exc_info=(type(error), error, error.__traceback__)
    )
    response = app.make_response(render_template('server_error.html', support_reference=support_reference))
    response.status_code = 500
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@app.get('/privacy')
def privacy(): return render_template('privacy.html')
def admin_required(fn):
    @wraps(fn)
    def wrapper(*a,**kw):
        admin_id = session.get('admin_id')
        if not admin_id or not db.session.get(AdminUser, admin_id):
            session.clear()
            return redirect(url_for('admin_login'))
        return fn(*a,**kw)
    return wrapper
@app.route(ADMIN_URL_PREFIX + '/logina',methods=['GET','POST'])
@app.route(ADMIN_URL_PREFIX + '/login',methods=['GET','POST'])  # legacy URL alias used by the existing site
@limiter.limit('8 per hour',methods=['POST'])
def admin_login():
    form=LoginForm()
    if form.validate_on_submit():
        user=AdminUser.query.filter_by(username=form.username.data.strip()).first()
        if user and check_password_hash(user.password_hash,form.password.data):
            selected_lang = session.get('lang', 'en'); session.clear(); session.permanent=True; session['admin_id']=user.id; session['lang']=selected_lang if selected_lang in LANGS else 'en'; return redirect(url_for('admin_dashboard'))
        flash(tr('invalid_credentials'),'error')
    return render_template('admin_login.html',form=form)
@app.get(ADMIN_URL_PREFIX)
@admin_required
def admin_dashboard():
    items = Inquiry.query.order_by(desc(Inquiry.created_at)).limit(250).all()
    return render_template(
        'admin.html', items=items, total_count=Inquiry.query.count(),
        new_count=Inquiry.query.filter_by(status='new').count(),
        reviewing_count=Inquiry.query.filter_by(status='reviewing').count(),
        priority_count=Inquiry.query.filter(Inquiry.urgency.in_(('high', 'critical'))).count()
    )
@app.get(ADMIN_URL_PREFIX + '/case/<int:case_id>')
@admin_required
def case_detail(case_id):
    item=Inquiry.query.get_or_404(case_id)
    return render_template('case_detail.html',item=item)
@app.get(ADMIN_URL_PREFIX + '/export.csv')
@admin_required
def export_inquiries():
    output=io.StringIO(newline='')
    writer=csv.writer(output)
    writer.writerow(['case_id','case_reference','name','email','topic','platform','urgency','risk_score','risk_flags','message','status','created_at_utc'])
    for item in Inquiry.query.order_by(desc(Inquiry.created_at)).all():
        writer.writerow([csv_safe(v) for v in [item.id,item.case_ref,item.name,item.email,item.topic,item.platform,item.urgency,item.risk_score,item.risk_flags,item.message,item.status,item.created_at.isoformat()]])
    return Response('\ufeff'+output.getvalue(),mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=yakuza-inquiries.csv','Cache-Control':'no-store'})
@app.post(ADMIN_URL_PREFIX + '/case/<int:case_id>')
@admin_required
def update_case(case_id):
    item=Inquiry.query.get_or_404(case_id); status=request.form.get('status')
    if status not in ('new','reviewing','closed'): abort(400)
    item.status=status; db.session.commit(); flash(tr('case_status_updated'),'success'); return redirect(url_for('admin_dashboard'))
@app.post(ADMIN_URL_PREFIX + '/logout')
@admin_required
def admin_logout(): session.clear(); return redirect(url_for('home'))
@app.get('/health')
def health(): return {'status':'ok','service':'yakuza'}, 200

@app.get('/health/intake')
def intake_health():
    """Safe diagnostic for DB reachability, WhatsApp number shape and runtime version."""
    database_status = 'unavailable'
    try:
        from sqlalchemy import text as sql_text
        db.session.execute(sql_text('SELECT 1'))
        database_status = 'reachable'
    except Exception as exc:
        db.session.rollback()
        app.logger.exception('intake_health_database_failed error_type=%s', type(exc).__name__)
    whatsapp_status = 'configured' if normalize_whatsapp_number(os.environ.get('WHATSAPP_NUMBER', '4917642484892')) else 'invalid_or_missing'
    healthy = database_status == 'reachable' and whatsapp_status == 'configured'
    return {
        'status': 'ok' if healthy else 'degraded',
        'database': database_status,
        'whatsapp_number': whatsapp_status,
        'python': sys.version.split()[0],
    }, (200 if healthy else 503)


@app.get('/health/db')
def database_health():
    try:
        from sqlalchemy import text as sql_text
        db.session.execute(sql_text('SELECT 1'))
        return {'status': 'ok', 'database': 'reachable'}, 200
    except Exception as exc:
        db.session.rollback()
        app.logger.exception('database_health_check_failed error_type=%s', type(exc).__name__)
        return {'status': 'error', 'database': 'unavailable'}, 503
with app.app_context():
    db.create_all()
    # Additive migration for existing SQLite/PostgreSQL deployments.
    from sqlalchemy import inspect, text
    cols={c['name'] for c in inspect(db.engine).get_columns('inquiry')}
    additions={'case_ref':'VARCHAR(32)','platform':"VARCHAR(40) DEFAULT 'not-specified'",'phone':"VARCHAR(40) DEFAULT ''",'incident_date':"VARCHAR(30) DEFAULT ''",'account_handle':"VARCHAR(120) DEFAULT ''",'evidence_url':"VARCHAR(500) DEFAULT ''",'urgency':"VARCHAR(20) DEFAULT 'normal'",'risk_score':'INTEGER DEFAULT 0','risk_flags':"TEXT DEFAULT ''",'triage_report':"TEXT DEFAULT ''",'contact_method':"VARCHAR(20) DEFAULT 'support'"}
    for col,definition in additions.items():
        if col not in cols: db.session.execute(text(f'ALTER TABLE inquiry ADD COLUMN {col} {definition}'))
    db.session.commit()
    # Existing databases upgraded with ALTER TABLE do not receive new model
    # constraints automatically. Enforce uniqueness for generated case references.
    ensure_unique_case_reference_index(db.engine)
    username=os.environ.get('ADMIN_USERNAME'); password=os.environ.get('ADMIN_PASSWORD')
    if username and password:
        admin=AdminUser.query.filter_by(username=username).first()
        password_change_requested = admin is None or os.environ.get('RESET_ADMIN_PASSWORD') == '1'
        if password_change_requested and len(password) < 16:
            raise RuntimeError('ADMIN_PASSWORD must contain at least 16 characters when creating or resetting the admin account.')
        if admin is None:
            db.session.add(AdminUser(username=username,password_hash=generate_password_hash(password))); db.session.commit()
        elif os.environ.get('RESET_ADMIN_PASSWORD') == '1':
            admin.password_hash=generate_password_hash(password); db.session.commit()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=False)
