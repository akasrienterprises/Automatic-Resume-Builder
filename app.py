from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, io, re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app=Flask(__name__); app.secret_key=os.environ.get('SECRET_KEY','dev-change-me')
DB='instance/resume_builder.db'; os.makedirs('instance',exist_ok=True)

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,password TEXT,created_at TEXT); CREATE TABLE IF NOT EXISTS resumes(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,title TEXT,data TEXT,created_at TEXT,updated_at TEXT);'''); c.commit(); c.close()
init()

def login_required(): return 'user_id' in session

def user():
 c=db(); r=c.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone(); c.close(); return r

@app.route('/')
def home(): return redirect(url_for('dashboard')) if login_required() else render_template('landing.html')
@app.route('/signup',methods=['GET','POST'])
def signup():
 if request.method=='POST':
  name=request.form['name'].strip(); email=request.form['email'].strip().lower(); p=request.form['password']
  if len(p)<6: flash('Password must be at least 6 characters.'); return redirect(url_for('signup'))
  try:
   c=db(); c.execute('INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)',(name,email,generate_password_hash(p),datetime.now().isoformat())); c.commit(); uid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.close(); session['user_id']=uid; return redirect(url_for('dashboard'))
  except sqlite3.IntegrityError: flash('Email already registered.')
 return render_template('auth.html',mode='signup')
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  c=db(); r=c.execute('SELECT * FROM users WHERE email=?',(request.form['email'].strip().lower(),)).fetchone(); c.close()
  if r and check_password_hash(r['password'],request.form['password']): session['user_id']=r['id']; return redirect(url_for('dashboard'))
  flash('Invalid email or password.')
 return render_template('auth.html',mode='login')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))
@app.route('/dashboard')
def dashboard():
 if not login_required(): return redirect(url_for('login'))
 c=db(); resumes=c.execute('SELECT * FROM resumes WHERE user_id=? ORDER BY updated_at DESC',(session['user_id'],)).fetchall(); count=c.execute('SELECT COUNT(*) FROM users').fetchone()[0]; total=c.execute('SELECT COUNT(*) FROM resumes').fetchone()[0]; c.close(); return render_template('dashboard.html',user=user(),resumes=resumes,user_count=count,resume_count=total)
@app.route('/resume/new',methods=['GET','POST'])
def resume_new(): return resume_edit(None)
@app.route('/resume/<int:rid>/edit',methods=['GET','POST'])
def resume_edit(rid):
 if not login_required(): return redirect(url_for('login'))
 c=db(); old=c.execute('SELECT * FROM resumes WHERE id=? AND user_id=?',(rid,session['user_id'])).fetchone() if rid else None
 if rid and not old: c.close(); return 'Not found',404
 if request.method=='POST':
  fields=['full_name','job_title','email','phone','location','summary','education','skills','projects','experience','certifications','achievements','languages','template','title']
  data={k:request.form.get(k,'').strip() for k in fields}; now=datetime.now().isoformat()
  import json
  if old: c.execute('UPDATE resumes SET title=?,data=?,updated_at=? WHERE id=? AND user_id=?',(data['title'] or 'My Resume',json.dumps(data),now,rid,session['user_id'])); new_id=rid
  else: c.execute('INSERT INTO resumes(user_id,title,data,created_at,updated_at) VALUES(?,?,?,?,?)',(session['user_id'],data['title'] or 'My Resume',json.dumps(data),now,now)); new_id=c.execute('SELECT last_insert_rowid()').fetchone()[0]
  c.commit(); c.close(); return redirect(url_for('preview',rid=new_id))
 c.close(); import json; data=json.loads(old['data']) if old else {'template':'classic'}; return render_template('builder.html',data=data,editing=bool(old))
@app.route('/resume/<int:rid>/preview')
def preview(rid):
 if not login_required(): return redirect(url_for('login'))
 c=db(); r=c.execute('SELECT * FROM resumes WHERE id=? AND user_id=?',(rid,session['user_id'])).fetchone(); c.close()
 if not r:return 'Not found',404
 import json; return render_template('preview.html',r=r,data=json.loads(r['data']))
@app.route('/resume/<int:rid>/delete',methods=['POST'])
def delete(rid):
 if not login_required(): return redirect(url_for('login'))
 c=db(); c.execute('DELETE FROM resumes WHERE id=? AND user_id=?',(rid,session['user_id'])); c.commit(); c.close(); return redirect(url_for('dashboard'))
@app.route('/resume/<int:rid>/pdf')
def pdf(rid):
 if not login_required(): return redirect(url_for('login'))
 c=db(); r=c.execute('SELECT * FROM resumes WHERE id=? AND user_id=?',(rid,session['user_id'])).fetchone(); c.close()
 if not r:return 'Not found',404
 import json; d=json.loads(r['data']); buf=io.BytesIO(); p=canvas.Canvas(buf,pagesize=A4); w,h=A4; x=45; y=h-55
 p.setTitle(d.get('title','Resume')); p.setFont('Helvetica-Bold',20); p.drawString(x,y,d.get('full_name','Your Name')); y-=22; p.setFont('Helvetica',10); p.drawString(x,y,' | '.join(v for v in [d.get('job_title'),d.get('email'),d.get('phone'),d.get('location')] if v)); y-=28
 for head,key in [('PROFESSIONAL SUMMARY','summary'),('EDUCATION','education'),('SKILLS','skills'),('PROJECTS','projects'),('EXPERIENCE','experience'),('CERTIFICATIONS','certifications'),('ACHIEVEMENTS','achievements'),('LANGUAGES','languages')]:
  txt=d.get(key,'');
  if not txt: continue
  p.setFont('Helvetica-Bold',11); p.drawString(x,y,head); y-=16; p.setFont('Helvetica',9.5)
  for para in txt.split('\n'):
   for line in re.findall('.{1,105}(?:\s+|$)',para) or [para]:
    if y<55: p.showPage(); y=h-55; p.setFont('Helvetica',9.5)
    p.drawString(x,y,line.strip()); y-=13
  y-=8
 p.save(); buf.seek(0); return send_file(buf,as_attachment=True,download_name='resume.pdf',mimetype='application/pdf')

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=True)
