// ============================================================
// WorkBuddy Body — Web Controller HTML Pages
// ============================================================
// Responsive web UI served from ESP32-C3 for controlling
// expressions, colors, speed, and canvas drawing.
// Stored in PROGMEM to save RAM.
// ============================================================

#ifndef WEB_PAGES_H
#define WEB_PAGES_H

#include <Arduino.h>

const char PAGE_INDEX[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>WorkBuddy — 表情控制</title>
<style>
  :root { --bg:#1a1a2e; --card:#16213e; --accent:#f5a623; --accent2:#e8850c; --text:#eee; --text2:#999; --border:#2a2a4a; --btn-bg:#0f3460; --btn-hover:#1a4a80; --radius:10px; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:var(--bg); color:var(--text); min-height:100vh; padding:12px; }
  .header { text-align:center; padding:12px 0; }
  .header h1 { font-size:1.4em; color:var(--accent); }
  .header p { color:var(--text2); font-size:0.75em; margin-top:2px; }
  .section { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:14px; margin-bottom:12px; }
  .section h2 { font-size:0.85em; color:var(--accent); margin-bottom:10px; text-transform:uppercase; letter-spacing:1px; }
  .btn-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; }
  .btn-grid-2 { display:grid; grid-template-columns:repeat(2, 1fr); gap:8px; }
  .btn { background:var(--btn-bg); color:var(--text); border:1px solid var(--border); border-radius:var(--radius); padding:12px 6px; font-size:0.85em; cursor:pointer; transition:all 0.15s; text-align:center; }
  .btn:hover { background:var(--btn-hover); }
  .btn:active { transform:scale(0.96); }
  .btn.active { background:var(--accent2); border-color:var(--accent); color:#000; font-weight:bold; }
  .btn .emoji { font-size:1.6em; display:block; margin-bottom:3px; }
  .btn .label { font-size:0.7em; color:var(--text2); }
  .btn.active .label { color:#4a3000; }
  .control-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
  .control-row label { font-size:0.8em; color:var(--text2); }
  input[type="range"] { -webkit-appearance:none; width:130px; height:6px; background:var(--border); border-radius:3px; outline:none; }
  input[type="range"]::-webkit-slider-thumb { -webkit-appearance:none; width:18px; height:18px; background:var(--accent); border-radius:50%; cursor:pointer; }
  input[type="color"] { -webkit-appearance:none; border:2px solid var(--border); border-radius:6px; width:38px; height:28px; cursor:pointer; background:transparent; }
  input[type="color"]::-webkit-color-swatch-wrapper { padding:2px; }
  input[type="color"]::-webkit-color-swatch { border-radius:3px; border:none; }
  .toggle-wrap { display:flex; align-items:center; gap:8px; }
  .toggle { width:44px; height:24px; background:var(--border); border-radius:12px; position:relative; cursor:pointer; transition:background 0.3s; }
  .toggle.on { background:var(--accent); }
  .toggle::after { content:''; position:absolute; top:2px; left:2px; width:20px; height:20px; background:white; border-radius:50%; transition:transform 0.3s; }
  .toggle.on::after { transform:translateX(20px); }
  #canvas-area { display:none; }
  #draw-canvas { border:2px solid var(--border); border-radius:var(--radius); display:block; margin:0 auto; touch-action:none; image-rendering:pixelated; }
  .canvas-btns { display:flex; gap:6px; margin-top:8px; justify-content:center; }
  .canvas-btns .btn { padding:8px 14px; font-size:0.75em; }
  .status { text-align:center; color:var(--text2); font-size:0.7em; padding:6px; }
</style>
</head>
<body>

<div class="header">
  <h1>一的表情面板</h1>
  <p>点击按钮切换表情</p>
</div>

<div class="section">
  <h2>常用表情</h2>
  <div class="btn-grid">
    <div class="btn active" data-expr="idle" onclick="setExpr(this)">
      <span class="emoji">&#9678;</span><span class="label">待机</span>
    </div>
    <div class="btn" data-expr="happy" onclick="setExpr(this)">
      <span class="emoji">&#9786;</span><span class="label">开心</span>
    </div>
    <div class="btn" data-expr="haha" onclick="setExpr(this)">
      <span class="emoji">&#128514;</span><span class="label">哈哈</span>
    </div>
    <div class="btn" data-expr="thinking" onclick="setExpr(this)">
      <span class="emoji">&#129300;</span><span class="label">思考中</span>
    </div>
    <div class="btn" data-expr="working" onclick="setExpr(this)">
      <span class="emoji">&#9881;</span><span class="label">工作中</span>
    </div>
    <div class="btn" data-expr="done" onclick="setExpr(this)">
      <span class="emoji">&#11088;</span><span class="label">完成!</span>
    </div>
    <div class="btn" data-expr="sleeping" onclick="setExpr(this)">
      <span class="emoji">&#128564;</span><span class="label">休眠</span>
    </div>
    <div class="btn" data-expr="boring" onclick="setExpr(this)">
      <span class="emoji">&#128530;</span><span class="label">无聊</span>
    </div>
    <div class="btn" data-expr="error" onclick="setExpr(this)">
      <span class="emoji">&#9888;</span><span class="label">出错</span>
    </div>
  </div>
</div>

<div class="section">
  <h2>设置</h2>
  <div class="control-row">
    <label>动画速度</label>
    <input type="range" id="speed" min="1" max="3" value="2" oninput="setSpeed(this.value)">
  </div>
  <div class="control-row">
    <label>背景色</label>
    <input type="color" id="bgcolor" value="#210421" onchange="setBg(this.value)">
  </div>
  <div class="control-row">
    <label>绘制色</label>
    <input type="color" id="pencolor" value="#fbe050" onchange="setPen(this.value)">
  </div>
  <div class="control-row">
    <label>显示器</label>
    <div class="toggle-wrap">
      <div class="toggle on" id="disp-toggle" onclick="toggleDisplay()"></div>
    </div>
  </div>
</div>

<div class="section">
  <h2>画布 / 其他</h2>
  <div class="btn-grid-2">
    <div class="btn" onclick="startCanvas()">
      <span class="emoji">&#9998;</span><span class="label">涂鸦</span>
    </div>
    <div class="btn" onclick="clearCanvas()">
      <span class="emoji">&#10060;</span><span class="label">清屏</span>
    </div>
  </div>
  <div id="canvas-area">
    <canvas id="draw-canvas" width="240" height="240"></canvas>
    <div class="canvas-btns">
      <div class="btn" onclick="exitCanvas()">退出涂鸦</div>
    </div>
  </div>
</div>

<div class="status" id="status">已连接</div>

<script>
function api(path) {
  fetch('/api/'+path).then(r=>r.text()).then(t=>{document.getElementById('status').textContent=t;}).catch(e=>{document.getElementById('status').textContent='Error';});
}
function setExpr(el) {
  document.querySelectorAll('[data-expr]').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  api('expr?name='+el.dataset.expr);
}
function setSpeed(v){api('speed?value='+v);}
function setBg(v){api('bg?color='+v.replace('#',''));}
function setPen(v){api('pen?color='+v.replace('#',''));}
function toggleDisplay(){
  var t=document.getElementById('disp-toggle');
  t.classList.toggle('on');
  api('display?state='+(t.classList.contains('on')?'1':'0'));
}
var canvas,ctx,drawing=false;
function startCanvas(){
  document.getElementById('canvas-area').style.display='block';
  canvas=document.getElementById('draw-canvas');
  ctx=canvas.getContext('2d');
  ctx.fillStyle='#210421';ctx.fillRect(0,0,240,240);
  canvas.onpointerdown=function(e){drawing=true;drawPixel(e);};
  canvas.onpointermove=function(e){if(drawing)drawPixel(e);};
  canvas.onpointerup=function(){drawing=false;};
  canvas.onpointerleave=function(){drawing=false;};
  api('expr?name=canvas');
}
function drawPixel(e){
  var rect=canvas.getBoundingClientRect();
  var sx=240/rect.width,sy=240/rect.height;
  var x=Math.floor((e.clientX-rect.left)*sx);
  var y=Math.floor((e.clientY-rect.top)*sy);
  var color=document.getElementById('pencolor').value;
  ctx.fillStyle=color;ctx.fillRect(x-1,y-1,3,3);
  api('pixel?x='+x+'&y='+y+'&color='+color.replace('#',''));
}
function clearCanvas(){
  if(ctx){ctx.fillStyle='#210421';ctx.fillRect(0,0,240,240);}
  api('clear');
}
function exitCanvas(){
  document.getElementById('canvas-area').style.display='none';
  var a=document.querySelector('[data-expr].active');
  if(a)api('expr?name='+a.dataset.expr);else api('expr?name=idle');
}
</script>
</body>
</html>
)rawliteral";

#endif // WEB_PAGES_H
