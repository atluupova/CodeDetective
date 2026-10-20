from flask import Flask, render_template, request, jsonify, session, redirect
import ast, io, sqlite3, contextlib, traceback, re, os, secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
DB = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'codedetective.db'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024

TRANSLATIONS = {
'kk': {'brand':'CodeDetective','tag':'Python қатесін тап, түсін, түзет','home':'Басты бет','checker':'Кодты тексеру','practice':'Жаттығулар','stats':'Статистика','about':'Жоба туралы','language':'Тіл','hero':'Python қателерін ақылды талдау','hero2':'Кодты енгізіңіз — жүйе қатені анықтап, дайын жауапты бермей, сатылы көмек ұсынады.','start':'Тексеруді бастау','demo':'Мысалды көру','code':'Python коды','run':'Тексеру','clear':'Тазалау','result':'Талдау нәтижесі','empty':'Код енгізіңіз','success':'Код синтаксистік тұрғыдан дұрыс.','hint':'Көмек','line':'Жол','error':'Қате түрі','output':'Шығыс','risk':'Қауіпсіздік үшін файл, жүйе және желі операциялары орындалмайды.','features':'Мүмкіндіктер','f1':'Қатені анықтау','f1d':'Python синтаксисін AST арқылы қауіпсіз тексереді.','f2':'3 сатылы Hint','f2d':'Дайын шешім орнына біртіндеп бағыт береді.','f3':'Зерттеу статистикасы','f3d':'Қате түрлері мен тексерулер SQLite базасына сақталады.','f4':'Екі тіл','f4d':'Қазақша және орысша интерфейс.','practice_title':'Python зертханасы','practice_desc':'Қате кодты зерттеп, көмек арқылы өзіңіз түзетіңіз.','stats_title':'Зерттеу панелі','stats_desc':'Нақты тексерулерден жиналған деректер.','total':'Барлық тексеру','correct':'Дұрыс код','errors':'Қате код','top_error':'Жиі қате','no_data':'Әзірге дерек жоқ','about_title':'CodeDetective зерттеу жобасы','about_text':'7–8 сынып оқушыларының Python бағдарламалауындағы типтік қателерін зерттеуге арналған цифрлық жүйе.','how':'Қалай жұмыс істейді?','step1':'Код енгізіледі','step2':'AST талдауы жасалады','step3':'Қате жіктеледі','step4':'Hint ұсынылады','step5':'Нәтиже базаға жазылады','sample':'Мысал код','exercise':'Тапсырма','check_answer':'Кодты тексеру','level':'Деңгей','all':'Барлығы','easy':'Жеңіл','medium':'Орташа','hard':'Күрделі','dashboard':'Панель','research':'Зерттеу','research_title':'Зерттеу режимі','research_desc':'Бастапқы және қорытынды тест арқылы прогресті өлшеңіз.','pretest':'Бастапқы тест','posttest':'Қорытынды тест','save_result':'Нәтижені сақтау','progress':'Прогресс','completed':'Орындалды','accuracy':'Дәлдік','continue':'Жалғастыру','research_result':'Зерттеу нәтижесі','before':'Бұрын','after':'Кейін','improvement':'Өзгеріс'},
'ru': {'brand':'CodeDetective','tag':'Найди, пойми и исправь ошибку Python','home':'Главная','checker':'Проверка кода','practice':'Практика','stats':'Статистика','about':'О проекте','language':'Язык','hero':'Умный анализ ошибок Python','hero2':'Введите код — система определит ошибку и даст пошаговые подсказки вместо готового ответа.','start':'Начать проверку','demo':'Посмотреть пример','code':'Код Python','run':'Проверить','clear':'Очистить','result':'Результат анализа','empty':'Введите код','success':'Код синтаксически корректен.','hint':'Подсказка','line':'Строка','error':'Тип ошибки','output':'Вывод','risk':'Для безопасности операции с файлами, системой и сетью не выполняются.','features':'Возможности','f1':'Поиск ошибок','f1d':'Безопасно проверяет синтаксис Python через AST.','f2':'3 уровня подсказок','f2d':'Направляет по шагам, не выдавая сразу готовое решение.','f3':'Статистика исследования','f3d':'Типы ошибок и проверки сохраняются в SQLite.','f4':'Два языка','f4d':'Интерфейс на казахском и русском.','practice_title':'Лаборатория Python','practice_desc':'Исследуйте ошибочный код и исправьте его с помощью подсказок.','stats_title':'Панель исследования','stats_desc':'Данные, собранные из реальных проверок.','total':'Всего проверок','correct':'Верный код','errors':'Код с ошибкой','top_error':'Частая ошибка','no_data':'Данных пока нет','about_title':'Исследовательский проект CodeDetective','about_text':'Цифровая система для исследования типичных ошибок Python у учащихся 7–8 классов.','how':'Как это работает?','step1':'Вводится код','step2':'Выполняется AST-анализ','step3':'Ошибка классифицируется','step4':'Выдается подсказка','step5':'Результат сохраняется','sample':'Пример кода','exercise':'Задание','check_answer':'Проверить код','level':'Уровень','all':'Все','easy':'Легкий','medium':'Средний','hard':'Сложный','dashboard':'Панель','research':'Исследование','research_title':'Режим исследования','research_desc':'Измерьте прогресс с помощью входного и итогового теста.','pretest':'Входной тест','posttest':'Итоговый тест','save_result':'Сохранить результат','progress':'Прогресс','completed':'Выполнено','accuracy':'Точность','continue':'Продолжить','research_result':'Результат исследования','before':'До','after':'После','improvement':'Изменение'},
'en': {'brand':'CodeDetective','tag':'Find, understand, fix Python errors','home':'Home','checker':'Code Checker','practice':'Practice','stats':'Statistics','about':'About','language':'Language','hero':'Smart Python Error Analysis','hero2':'Enter code — the system identifies errors and gives progressive hints instead of an instant solution.','start':'Start checking','demo':'View example','code':'Python code','run':'Analyze','clear':'Clear','result':'Analysis result','empty':'Enter some code','success':'The code is syntactically correct.','hint':'Hint','line':'Line','error':'Error type','output':'Output','risk':'For safety, file, system and network operations are not executed.','features':'Features','f1':'Error detection','f1d':'Safely checks Python syntax using AST.','f2':'3-level hints','f2d':'Guides step by step instead of revealing the full answer.','f3':'Research statistics','f3d':'Error types and checks are stored in SQLite.','f4':'Three languages','f4d':'Kazakh, Russian and English interface.','practice_title':'Python Lab','practice_desc':'Investigate buggy code and fix it using progressive hints.','stats_title':'Research Dashboard','stats_desc':'Data collected from real code checks.','total':'Total checks','correct':'Correct code','errors':'Code with errors','top_error':'Top error','no_data':'No data yet','about_title':'CodeDetective Research Project','about_text':'A digital system for studying typical Python programming errors among grade 7–8 students.','how':'How it works','step1':'Code is entered','step2':'AST analysis runs','step3':'Error is classified','step4':'A hint is offered','step5':'Result is stored','sample':'Sample code','exercise':'Exercise','check_answer':'Check code','level':'Level','all':'All','easy':'Easy','medium':'Medium','hard':'Hard','dashboard':'Dashboard','research':'Research','research_title':'Research Mode','research_desc':'Measure progress with a pre-test and post-test.','pretest':'Pre-test','posttest':'Post-test','save_result':'Save result','progress':'Progress','completed':'Completed','accuracy':'Accuracy','continue':'Continue','research_result':'Research result','before':'Before','after':'After','improvement':'Change'} }

HINTS={
'SyntaxError':{
'kk':['Код құрылымын мұқият тексер.','Жақша, тырнақша және қос нүктелерді тексер.','if, for, while, def жолдарының соңында : белгісі бар ма?'],
'ru':['Проверь структуру кода.','Проверь скобки, кавычки и двоеточия.','Есть ли : после if, for, while или def?'],
'en':['Check the structure of the code.','Check brackets, quotes and colons.','Is there a : after if, for, while or def?']},
'IndentationError':{
'kk':['Жолдардың шегінісіне назар аудар.','Бір блоктағы жолдар бірдей шегіністе болуы керек.','if/for/while ішіндегі командаларды 4 бос орынмен шегіндір.'],
'ru':['Обрати внимание на отступы.','Строки одного блока должны иметь одинаковый отступ.','Сделай отступ 4 пробела внутри if/for/while.'],
'en':['Pay attention to indentation.','Lines in the same block need equal indentation.','Indent statements inside if/for/while by 4 spaces.']},
'NameError':{
'kk':['Айнымалы атауын тексер.','Айнымалы қолданылмай тұрып анықталды ма?','Үлкен-кіші әріп пен жазылуын барлық жерде салыстыр.'],
'ru':['Проверь имя переменной.','Определена ли переменная до использования?','Сравни регистр и написание имени во всех местах.'],
'en':['Check the variable name.','Was the variable defined before use?','Compare spelling and letter case everywhere.']},
'TypeError':{
'kk':['Амалға қатысатын мәндердің типін тексер.','input() нәтижесі мәтін екенін есте сақта.','Қажет болса int(), float() немесе str() арқылы түрлендір.'],
'ru':['Проверь типы значений в операции.','Помни: input() возвращает строку.','При необходимости используй int(), float() или str().'],
'en':['Check the value types used in the operation.','Remember: input() returns a string.','Convert with int(), float() or str() if needed.']},
'IndexError':{
'kk':['Тізім индексін тексер.','Индекстер 0-ден басталады.','len(тізім)-1 ең соңғы жарамды индекс екенін тексер.'],
'ru':['Проверь индекс списка.','Индексы начинаются с 0.','Последний допустимый индекс равен len(список)-1.'],
'en':['Check the list index.','Indexes start at 0.','The last valid index is len(list)-1.']}}

EXERCISES=[
 {'id':1,'level':'easy','code':'for i in range(5)\n    print(i)','kind':'SyntaxError'},
 {'id':2,'level':'easy','code':'if 7 > 3:\nprint("OK")','kind':'IndentationError'},
 {'id':3,'level':'easy','code':'name = "Asilzhan"\nprint(nam)','kind':'NameError'},
 {'id':4,'level':'easy','code':'numbers = [10, 20, 30]\nprint(numbers[3])','kind':'IndexError'},
 {'id':5,'level':'medium','code':'age = "13"\nprint(age + 2)','kind':'TypeError'},
 {'id':6,'level':'medium','code':'score = 15\nprint(Score)','kind':'NameError'},
 {'id':7,'level':'medium','code':'if 10 > 5\n    print("Yes")','kind':'SyntaxError'},
 {'id':8,'level':'medium','code':'for x in range(3):\nprint(x * 2)','kind':'IndentationError'},
 {'id':9,'level':'medium','code':'items = ["a", "b"]\nprint(items[5])','kind':'IndexError'},
 {'id':10,'level':'medium','code':'price = "250"\nprint(price / 2)','kind':'TypeError'},
 {'id':11,'level':'hard','code':'total = 25\nprint(totl + 5)','kind':'NameError'},
 {'id':12,'level':'hard','code':'for n in range(1, 6)\n    print(n ** 2)','kind':'SyntaxError'},
 {'id':13,'level':'hard','code':'values = [3, 6, 9, 12]\nprint(values[4])','kind':'IndexError'},
 {'id':14,'level':'hard','code':'count = "5"\nresult = count + 10\nprint(result)','kind':'TypeError'},
 {'id':15,'level':'hard','code':'if True:\nprint("Python")\n    print("CodeDetective")','kind':'IndentationError'}]

def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; return con

def init_db():
    con=db(); con.execute('''CREATE TABLE IF NOT EXISTS checks(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, lang TEXT, status TEXT, error_type TEXT, line_no INTEGER)'''); con.execute('''CREATE TABLE IF NOT EXISTS research_results(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, phase TEXT, score INTEGER, total INTEGER)'''); con.commit(); con.close()
init_db()

def lang(): return session.get('lang','kk') if session.get('lang','kk') in ('kk','ru') else 'kk'
def t(): return TRANSLATIONS[lang()]

@app.context_processor
def inject(): return dict(T=t(), current_lang=lang())

@app.route('/lang/<code>')
def setlang(code):
    if code in ('kk', 'ru'):
        session['lang'] = code
        session.modified = True
    return redirect(request.referrer or '/')

@app.route('/')
def index(): return render_template('index.html')
@app.route('/checker')
def checker(): return render_template('checker.html')
@app.route('/practice')
def practice(): return render_template('practice.html', exercises=EXERCISES)
@app.route('/about')
def about(): return render_template('about.html')
@app.route('/stats')
def stats():
    con=db(); total=con.execute('SELECT COUNT(*) c FROM checks').fetchone()['c']; correct=con.execute("SELECT COUNT(*) c FROM checks WHERE status='success'").fetchone()['c'];
    rows=con.execute("SELECT error_type,COUNT(*) c FROM checks WHERE error_type IS NOT NULL GROUP BY error_type ORDER BY c DESC").fetchall(); con.close()
    labels=[r['error_type'] for r in rows]; values=[r['c'] for r in rows]; top=labels[0] if labels else '—'
    return render_template('stats.html', total=total, correct=correct, errors=total-correct, top=top, labels=labels, values=values)


@app.route('/dashboard')
def dashboard():
    con=db()
    total=con.execute('SELECT COUNT(*) c FROM checks').fetchone()['c']
    correct=con.execute("SELECT COUNT(*) c FROM checks WHERE status='success'").fetchone()['c']
    rows=con.execute("SELECT error_type,COUNT(*) c FROM checks WHERE error_type IS NOT NULL GROUP BY error_type ORDER BY c DESC").fetchall()
    rr=con.execute("SELECT phase,score,total FROM research_results ORDER BY id DESC").fetchall(); con.close()
    research={}
    for r in rr:
        if r['phase'] not in research: research[r['phase']]=(r['score'],r['total'])
    accuracy=round(correct/total*100) if total else 0
    return render_template('dashboard.html', total=total, correct=correct, errors=total-correct, accuracy=accuracy, rows=rows, research=research)

@app.route('/research')
def research():
    con=db(); rr=con.execute("SELECT phase,score,total FROM research_results ORDER BY id DESC").fetchall(); con.close()
    data={}
    for r in rr:
        if r['phase'] not in data: data[r['phase']]={'score':r['score'],'total':r['total']}
    return render_template('research.html', research=data)

@app.post('/api/research')
def save_research():
    data=request.get_json(silent=True) or {}; phase=data.get('phase'); score=int(data.get('score',0)); total=int(data.get('total',5))
    if phase not in ('pre','post'): return jsonify({'ok':False}),400
    con=db(); con.execute('INSERT INTO research_results(created_at,phase,score,total) VALUES(?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),phase,score,total)); con.commit(); con.close()
    return jsonify({'ok':True})

DANGEROUS=(ast.Import,ast.ImportFrom,ast.With,ast.AsyncWith,ast.Global,ast.Nonlocal,ast.Delete)
BLOCKED_NAMES={'open','exec','eval','compile','__import__','globals','locals','vars','getattr','setattr','delattr','input','help','breakpoint'}

def safety_check(tree):
    for n in ast.walk(tree):
        if isinstance(n,DANGEROUS): return False
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in BLOCKED_NAMES: return False
        if isinstance(n,ast.Attribute) and (n.attr.startswith('__') or n.attr in {'system','popen','remove','unlink'}): return False
    return True

def infer_runtime_error(tree):
    # Conservative static patterns for educational examples; no arbitrary code execution.
    assigned=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): assigned.add(n.id)
    builtins={'print','range','len','int','str','float','list','max','min','sum','True','False','None'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id not in assigned and n.id not in builtins:
            return 'NameError', getattr(n,'lineno',None)
    for n in ast.walk(tree):
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add):
            if (isinstance(n.left,ast.Constant) and isinstance(n.right,ast.Constant) and type(n.left.value)!=type(n.right.value)):
                return 'TypeError', getattr(n,'lineno',None)
    env={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,(ast.List,ast.Tuple,ast.Constant)):
            try: env[n.targets[0].id]=ast.literal_eval(n.value)
            except: pass
    for n in ast.walk(tree):
        if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id in env and isinstance(env[n.value.id],(list,tuple)):
            try:
                idx=ast.literal_eval(n.slice)
                if isinstance(idx,int) and not (-len(env[n.value.id]) <= idx < len(env[n.value.id])): return 'IndexError', getattr(n,'lineno',None)
            except: pass
    return None,None

@app.post('/api/check')
def api_check():
    data=request.get_json(silent=True) or {}; code=(data.get('code') or '').strip(); L=lang()
    if not isinstance(code, str) or len(code) > 4000:
        return jsonify({'status':'error','message':'Код тым ұзын (ең көбі 4000 таңба).'}), 400
    if not code: return jsonify({'status':'empty','message':TRANSLATIONS[L]['empty']})
    try:
        tree=ast.parse(code)
        if not safety_check(tree):
            status='blocked'; et='SafetyRestriction'; line=None
            msg={'kk':'Қауіпсіздікке байланысты бұл команда орындалмайды.','ru':'Эта команда заблокирована из соображений безопасности.','en':'This command is blocked for safety.'}[L]
            hints=[TRANSLATIONS[L]['risk']]
        else:
            et,line=infer_runtime_error(tree)
            if et:
                status='error'; msg=et; hints=HINTS.get(et,{}).get(L,[])
            else:
                status='success'; et=None; line=None; msg=TRANSLATIONS[L]['success']; hints=[]
    except (IndentationError, SyntaxError) as e:
        et='IndentationError' if isinstance(e,IndentationError) else 'SyntaxError'; line=e.lineno; status='error'; msg=et; hints=HINTS[et][L]
    con=db(); con.execute('INSERT INTO checks(created_at,lang,status,error_type,line_no) VALUES(?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),L,status,et,line)); con.commit(); con.close()
    return jsonify({'status':status,'error_type':et,'line':line,'message':msg,'hints':hints})

if __name__=='__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
