import os,re,json,hmac,secrets
from datetime import datetime
from urllib.parse import quote,urlparse
from flask import Flask,render_template,request,redirect,url_for,session,flash,abort
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from models import db,Case,AdminNote,AuditLog
from services.i18n import tr
from services.risk import assess_risk
csrf=CSRFProtect()
limiter=Limiter(key_func=get_remote_address,default_limits=["200 per hour"],storage_uri=os.getenv("RATELIMIT_STORAGE_URI","memory://"))
def whatsapp_link(number, message):
 digits=re.sub(r"\D","",number or "")
 if not digits:return None
 return "https://wa.me/"+digits+"?text="+quote(message)

def create_app():
 app=Flask(__name__);app.config.from_object(Config);db.init_app(app);csrf.init_app(app);limiter.init_app(app)
 def lang(): return session.get("lang","en")
 @app.context_processor
 def inject(): return {"t":lambda k,**kw:tr(lang(),k,**kw),"lang":lang(),"direction":"rtl" if lang() in ("ar","ar-tn") else "ltr","csrf_token":lambda:__import__("flask_wtf.csrf",fromlist=["generate_csrf"]).generate_csrf()}
 @app.before_request
 def permanent(): session.permanent=True
 @app.after_request
 def headers(r):
  r.headers["X-Content-Type-Options"]="nosniff";r.headers["X-Frame-Options"]="DENY";r.headers["Referrer-Policy"]="strict-origin-when-cross-origin";r.headers["Permissions-Policy"]="camera=(),microphone=(),geolocation=()"
  r.headers["Content-Security-Policy"]="default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'"
  if request.is_secure:r.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
  return r
 @app.get("/language/<code>")
 def language(code):
  if code not in ("en","fr","ar","ar-tn"):abort(404)
  session["lang"]=code;dest=request.args.get("next","/")
  return redirect(dest if dest.startswith("/") and not dest.startswith("//") else "/")
 @app.get("/")
 def index():return render_template("index.html")
 @app.get("/about")
 def about():return render_template("about.html")
 @app.route("/intake",methods=["GET","POST"])
 @limiter.limit("5 per hour",methods=["POST"])
 def intake():
  if request.method=="GET":
   a,b=secrets.randbelow(8)+2,secrets.randbelow(8)+2;session["human"]=str(a+b);session["human_time"]=datetime.utcnow().timestamp()
   return render_template("intake.html",a=a,b=b)
  answer=request.form.get("human_answer","").strip();expected=session.pop("human",None);issued=session.pop("human_time",0)
  if not expected or datetime.utcnow().timestamp()-issued>600 or not hmac.compare_digest(str(expected),answer):
   flash("Human check failed. Please try again.","error");return redirect(url_for("intake"))
  if request.form.get("website",""):abort(400)
  def val(k,n,required=False):
   x=request.form.get(k,"")
   if not isinstance(x,str):raise ValueError("Invalid field")
   x=x.strip()
   if required and not x:raise ValueError("Please complete required fields.")
   if len(x)>n or any(ord(c)<32 and c not in "\n\t" for c in x):raise ValueError("Invalid or overlong field.")
   return x
  try:
   name=val("name",100,True);email=val("email",254,True).lower();platform=val("platform",40,True);handle=val("handle",200);phone=val("phone",32);date=val("incident_date",10);category=val("category",40,True);priority=val("priority",16,True);evidence=val("evidence_url",500);description=val("description",5000,True);nextstep=val("preferred_next_step",20,True)
   if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email):raise ValueError("Enter a valid email.")
   if len(description)<25:raise ValueError("Description must contain at least 25 characters.")
   if platform not in ["Not specified","Instagram","Facebook","TikTok","Google","X","LinkedIn","Other"]:raise ValueError("Invalid platform.")
   if category not in ["recovery","risk","impersonation","scam","privacy","reputation","compliance","security","other"] or priority not in ["normal","high","critical"] or nextstep not in ["inbox","whatsapp"]:raise ValueError("Invalid selection.")
   if evidence and (urlparse(evidence).scheme!="https" or not urlparse(evidence).netloc):raise ValueError("Evidence link must use HTTPS.")
   if date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date):raise ValueError("Invalid incident date.")
   if not request.form.get("consent"):raise ValueError("Consent is required.")
  except ValueError as e:
   flash(str(e),"error");a,b=3,4;session["human"]="7";session["human_time"]=datetime.utcnow().timestamp();return render_template("intake.html",a=a,b=b),400
  risk=assess_risk(description,evidence);ref="YKZ-"+datetime.utcnow().strftime("%y%m%d")+"-"+secrets.token_hex(3).upper()
  c=Case(reference=ref,language=lang(),name=name,email=email,platform=platform,handle=handle or None,phone=phone or None,incident_date=date or None,category=category,priority=priority,evidence_url=evidence or None,description=description,preferred_next_step=nextstep,risk_score=risk["score"],risk_flags_json=json.dumps(risk["flags"],ensure_ascii=False))
  db.session.add(c);db.session.flush();db.session.add(AuditLog(actor="public",action="case_created",case_reference=ref,detail="Intake submitted"));db.session.commit()
  # The database commit happens before any WhatsApp action. WhatsApp is a
  # user-initiated click-to-chat handoff; the website never sends messages silently.
  support_number=os.getenv("WHATSAPP_NUMBER","")
  message=(f"Hello YAKUZA, my case {ref} has been recorded. "
           f"Name: {name}. Request: {category}. Priority: {priority}. "
           "Please advise on the next steps.")
  wa_url=whatsapp_link(support_number,message)
  return render_template("intake_success.html",case=c,whatsapp_url=wa_url,preferred_next_step=nextstep)
 @app.route("/status",methods=["GET","POST"])
 @limiter.limit("10 per hour",methods=["POST"])
 def status():
  result=None;searched=request.method=="POST"
  if searched and app.config["PUBLIC_STATUS_LOOKUP"]:
   ref=request.form.get("reference","").strip().upper();email=request.form.get("email","").strip().lower()
   if len(ref)<=24 and len(email)<=254:result=Case.query.filter_by(reference=ref,email=email).first()
  return render_template("status_lookup.html",result=result,searched=searched)
 def admin(): 
  if not session.get("admin"):abort(403)
 @app.route("/admin/login",methods=["GET","POST"])
 @limiter.limit("10 per hour",methods=["POST"])
 def admin_login():
  if request.method=="POST":
   u=request.form.get("username","");p=request.form.get("password","");eu=app.config["ADMIN_USERNAME"];ep=app.config["ADMIN_PASSWORD"]
   ok=bool(eu and ep) and hmac.compare_digest(u,eu) and hmac.compare_digest(p,ep)
   if ok:
    session.clear();session["admin"]=True;session["admin_user"]=eu;session.permanent=True;db.session.add(AuditLog(actor=eu,action="admin_login"));db.session.commit();return redirect(url_for("dashboard"))
   db.session.add(AuditLog(actor="unknown",action="admin_login_failed"));db.session.commit();flash("Invalid credentials.","error")
  return render_template("admin_login.html")
 @app.post("/admin/logout")
 def logout():
  admin();db.session.add(AuditLog(actor=session.get("admin_user","admin"),action="logout"));db.session.commit();session.clear();return redirect(url_for("admin_login"))
 @app.get("/admin")
 def dashboard():
  admin();f=request.args.get("status","all");q=Case.query
  if f in ("new","reviewing","waiting","resolved","closed"):q=q.filter_by(status=f)
  cases=q.order_by(Case.created_at.desc()).limit(300).all();logs=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(30).all()
  return render_template("admin_dashboard.html",cases=cases,logs=logs,selected=f)
 @app.route("/admin/case/<reference>",methods=["GET","POST"])
 def case_detail(reference):
  admin();c=Case.query.filter_by(reference=reference).first_or_404()
  if request.method=="POST":
   state=request.form.get("status","");note=request.form.get("note","").strip()
   if state not in ("new","reviewing","waiting","resolved","closed") or len(note)>2000:abort(400)
   c.status=state
   if note:db.session.add(AdminNote(case_id=c.id,author=session.get("admin_user","admin"),body=note))
   db.session.add(AuditLog(actor=session.get("admin_user","admin"),action="case_updated",case_reference=c.reference,detail=state));db.session.commit();flash("Case updated.","success");return redirect(url_for("case_detail",reference=reference))
  client_wa=whatsapp_link(c.phone, f"Hello {c.name}, this is YAKUZA regarding case {c.reference}. We would like to follow up on your request.")
  return render_template("admin_case.html",case=c,flags=json.loads(c.risk_flags_json or "[]"),client_whatsapp_url=client_wa)
 @app.get("/healthz")
 def healthz():
  try:db.session.execute(db.text("SELECT 1"));return {"status":"ok","database":"reachable"},200
  except Exception:return {"status":"degraded"},503
 @app.errorhandler(429)
 def limited(e):return render_template("error.html",code=429,message="Too many requests. Try later."),429
 with app.app_context():db.create_all()
 return app
app=create_app()
