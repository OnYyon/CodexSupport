"""Build an offline cinematic learning journey from the current Markdown and local sources."""
from pathlib import Path
import sys,re,json,base64
import markdown
from markdown.extensions.toc import slugify_unicode
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'battle-journey'))
from content import make_questions
source=(root/'OOP_CPP20_Полная_подготовка_к_контрольной.md').read_text()
bank=make_questions()
titles=['Язык, типы и инициализация','Операторы и управление','Память, указатели и ссылки','Функции и передача данных','Классы и инкапсуляция','Время жизни, RAII и copy/move','Перегрузка операторов','Наследование и полиморфизм']
places=['Врата начала','Кузница решений','Лес памяти','Мост функций','Архив классов','Руины времени','Чертог символов','Цитадель наследования']
epigraphs=['Каждое состояние должно обрести смысл.','Путь начинается с правильного условия.','Адрес не даёт права владеть.','Передать — не всегда скопировать.','Защити закон внутреннего мира.','Всё полученное должно быть освобождено.','Знакомый символ должен сохранять смысл.','Разные истории говорят на одном языке.']
enemies=['Страж неопределённости','Голем условий','Пожиратель адресов','Страж перегрузок','Хранитель инварианта','Похититель ресурсов','Ложный символ','Срезающий страж']
victories=['Ты отличил создание объекта от чтения неизвестного значения. Впереди — решения и порядок действий.','Условия стали точными, а действия — осмысленными. Дальше дорога уходит в лес памяти.','Теперь ты различаешь владение и наблюдение. Мост впереди проверит, как передаются данные.','Ссылка, копия и самостоятельный результат заняли свои места. В архиве из них родятся классы.','Внутренний закон объекта защищён. Теперь нужно понять, кто отвечает за его время жизни.','Ресурсы больше не остаются без владельца. Настало время дать операциям точные имена.','За привычными символами стоят понятные контракты. Цитадель проверит отношения между типами.','Ты связал восемь тем: от первого значения до полиморфного поведения. Теперь объясни эту картину собственными словами.']
lectures={}
for match in re.finditer(r'^# Лекция ([1-8])\.[^\n]*\n(.*?)(?=^# |\Z)',source,re.M|re.S):lectures[int(match[1])]=match[2]
assert set(lectures)==set(range(1,9))
templates=[];stages=[]
for n in range(1,9):
 text=lectures[n];blocks=re.split(r'(?=^## \d+\.)',text,flags=re.M);intro=markdown.markdown(blocks[0],extensions=['fenced_code','tables','sane_lists','toc'],extension_configs={'toc':{'slugify':slugify_unicode}})
 html='<section class="lesson-section" data-topic="'+str(n)+'.0" id="sec-'+str(n)+'-0">'+intro+'</section>'
 sections=[]
 for block in blocks[1:]:
  m=re.match(r'## (\d+\.\d+)\.\s*(.*?)\n',block)
  if not m:continue
  topic=m[1];label=m[1]+'. '+m[2];sections.append(dict(topic=topic,title=label));body=markdown.markdown(block,extensions=['fenced_code','tables','sane_lists','toc'],extension_configs={'toc':{'slugify':slugify_unicode}})
  html+='<section class="lesson-section" data-topic="'+topic+'" id="sec-'+topic.replace('.','-')+'">'+body+'</section>'
 def embed(m):
  p=root/m[1]
  return 'src="data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode()+'"'
 html=re.sub(r'src="(assets/[^\"]+\.svg)"',embed,html)
 templates.append('<template id="lesson-template-'+str(n)+'">'+html+'</template>')
 words=len(re.findall(r'\S+',text));stages.append(dict(id=n,title=titles[n-1],place=places[n-1],enemy=enemies[n-1],epigraph=epigraphs[n-1],victory=victories[n-1],minutes=max(5,round(words/180)),sections=sections,questions=bank[n]))
 for q in bank[n]:assert any(x['topic']==q['topic'] for x in sections),(n,q['topic'])
assets={}
# Sprite assets are retained only for devices without WebGL.
for name,filename in [('environment','cinematic-environments.png'),('knight','battle-knight-actions.png'),('monsters','battle-monsters.png')]:assets[name]='data:image/png;base64,'+base64.b64encode((root/'assets'/filename).read_bytes()).decode()
data=json.dumps(dict(stages=stages,assets=assets),ensure_ascii=False).replace('</','<\\/')
style=(root/'battle-journey/style.css').read_text()
page=r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0b121c"><meta name="color-scheme" content="dark"><title>C++ / The Isometric Journey</title><style>__STYLE__</style></head><body>
<a href="#reader-title" class="skip">Перейти к материалу</a><canvas id="scene" role="img" aria-label="Объёмный рыцарь идёт по трёхмерной дороге в изометрической перспективе и побеждает монстров за верные ответы"></canvas><div class="grade"></div><div class="texture"></div><div class="frame-bottom"></div>
<header class="hud"><a class="brand" href="#" aria-label="C++ — путь понимания"><em>C++</em> / ПУТЬ ПОНИМАНИЯ</a><div class="hud-line"><i id="route-progress"></i></div><span class="hud-status" id="hud-status"></span><nav aria-label="Управление путешествием"><button id="map-button">Главы</button><button id="library-button">Библиотека</button><button id="motion" aria-pressed="true">MOTION ON</button></nav></header>
<main>
<section class="screen intro" id="intro"><div class="intro-copy"><div class="eyebrow">ВОСЕМЬ ГЛАВ / ОДНА ДОРОГА</div><h1>Каждый ответ<br><em>меняет путь.</em></h1><p>Рыцарь идёт вперёд, когда знание становится пониманием. Прочитай главу — и встреть её стража на дороге.</p><p>Верный ответ запускает удар. Пять ударов побеждают монстра. Две ошибки возвращают к тем правилам, которые стоит повторить.</p><div class="actions"><button class="primary" id="start">Начать путь</button><button class="secondary" data-library>Сначала открыть конспект</button></div><div class="intro-notes"><div><strong>08</strong><span>ЛЕКЦИЙ</span></div><div><strong>48</strong><span>ВОПРОСОВ</span></div><div><strong>05</strong><span>УДАРОВ ДО ПОБЕДЫ</span></div></div><p id="intro-progress" style="font:8px var(--mono);margin-top:20px;letter-spacing:1px">Читай. Отвечай. Продвигайся.</p></div></section>
<section class="screen read-screen" id="read-screen" hidden aria-label="Чтение главы"><div class="reader-label"><span class="tiny" id="road-name"></span><strong id="road-theme"></strong><p>Сначала прочитай материал. Когда будешь готов — выйди на дорогу и проверь понимание.</p></div><div class="read-hint">ДОРОГА ОТКРЫВАЕТСЯ<br>ПОСЛЕ ПЯТИ ВЕРНЫХ ОТВЕТОВ.</div><article class="reader"><div class="reader-top"><div class="eyebrow" id="reader-kicker"></div><h2 id="reader-title" tabindex="-1"></h2><div class="reader-meta"><span id="reader-length"></span><span id="reading-percentage">0% прочитано</span></div></div><div class="reader-progress"><i id="reading-bar"></i></div><div class="reader-body" id="reader-body" tabindex="0" aria-label="Текст лекции"></div><footer class="reader-footer"><small id="read-phase-note"></small><button class="primary" id="reader-start">Выйти на дорогу</button></footer></article></section>
<section class="screen battle-screen" id="battle-screen" hidden aria-label="Сражение вопросами"><div class="enemy-hud"><span class="label" id="enemy-subtitle"></span><h2 id="enemy-name"></h2><div class="enemy-health" id="enemy-health" role="img" aria-label="Здоровье противника"></div></div><div class="lives">ПРАВО НА ОШИБКУ<strong id="lives-value">2 / 2</strong></div><div class="battle-word" id="battle-word" aria-hidden="true"></div><article class="question-panel"><div class="question-eyebrow"><span id="question-count"></span><span id="battle-question-meta"></span></div><h3 id="question-title" tabindex="-1"></h3><div class="question-grid"><pre class="question-code" id="question-code"></pre><div class="answers" id="answers"></div></div><div class="feedback" id="question-feedback" role="status" aria-live="polite"></div></article></section>
<section class="outcome" id="outcome" hidden><div class="outcome-card"><div class="eyebrow" id="outcome-kicker"></div><h2 id="outcome-title" tabindex="-1"></h2><p id="outcome-text"></p><div class="actions"><button class="primary" id="next-stage">Продолжить путь</button><button class="secondary" data-library>Вернуться к конспекту</button></div><div class="final-score" id="outcome-explanation"></div></div></section>
<section class="travel-title" id="travel" hidden aria-live="polite"><span id="travel-kicker"></span><h2 id="travel-title"></h2><p id="travel-text"></p></section>
</main><nav class="chapter-rail" aria-label="Главы путешествия">__RAIL__</nav><div class="location" id="location"></div><div class="toast" id="toast" role="status" aria-live="polite"></div><div class="loader" id="loader"><strong id="loader-title">Дорога проступает из тумана.</strong><small id="loader-subtitle">ЗАГРУЖАЕМ МИР И ЕГО ИСТОРИИ</small></div>
<dialog id="library" aria-labelledby="library-title"><div class="dialog-head"><h2 id="library-title">Библиотека C++</h2><button data-close="library" aria-label="Закрыть библиотеку">Закрыть ×</button></div><div class="dialog-controls"><input id="library-search" type="search" placeholder="Найти правило, тип, оператор…" aria-label="Поиск в конспекте"><select id="library-filter" aria-label="Выбор лекции"><option value="all">Весь конспект</option>__OPTIONS__</select></div><div class="dialog-body" id="library-body"><p id="library-empty" class="empty" hidden>По этому запросу ничего не найдено.</p></div></dialog>
<dialog id="map" aria-labelledby="map-title"><div class="dialog-head"><h2 id="map-title">Дорога восьми знаний</h2><button data-close="map" aria-label="Закрыть главы">Закрыть ×</button></div><div class="dialog-body" id="map-body" style="height:calc(100% - 80px)"></div></dialog>
__TEMPLATES__<script id="journey-data" type="application/json">__DATA__</script><script>__MODEL__</script><script>__THREE__</script><script>__SCENE__</script><script>__SCENE3D__</script><script>__APP__</script></body></html>'''
values={'__THREE__':(root/'battle-journey/vendor/three.min.js').read_text()+'\n/* Three.js MIT license: '+(root/'battle-journey/vendor/THREE-LICENSE.txt').read_text()+' */','__SCENE3D__':(root/'battle-journey/scene3d.js').read_text(),'__STYLE__':style,'__RAIL__':''.join(f'<button aria-label="Лекция {i}">{i:02}</button>' for i in range(1,9)),'__OPTIONS__':''.join(f'<option value="{i}">Лекция {i+1}</option>' for i in range(8)),'__TEMPLATES__':''.join(templates),'__DATA__':data,'__MODEL__':(root/'battle-journey/model.js').read_text(),'__SCENE__':(root/'battle-journey/scene.js').read_text(),'__APP__':(root/'battle-journey/app.js').read_text()}
for key,value in values.items():page=page.replace(key,value)
output=root/'OOP_CPP20_Battle_Journey.html';output.write_text(page)
print(f'Built {output.name}: {len(page.encode())/1048576:.2f} MiB; 8 full lectures; 48 questions; 3D isometric world + offline sprite fallback.')
