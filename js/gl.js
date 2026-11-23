/* Attractive Home — WebGL layers (three.js) */
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const root = document.documentElement;
const AH = window.AH || { process: { a: 0, b: 0 }, mat: { index: 0, count: 6, on: [] }, listeners: [] };
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const coarse = matchMedia('(pointer: coarse)').matches;
const DPR = Math.min(window.devicePixelRatio || 1, coarse ? 1.5 : 1.75);
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

function webglOK() {
  try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch (e) { return false; }
}

const loader = new THREE.TextureLoader();
const loadTex = (url, srgb) => new Promise((res, rej) => loader.load(url, t => {
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; res(t);
}, undefined, rej));

const NOISE = /* glsl */`
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453123); }
float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x), mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.,1.)),f.x), f.y); }
float fbm(vec2 p){ float v=0., a=.5; for(int i=0;i<4;i++){ v+=a*noise(p); p*=2.03; a*=.5; } return v; }
vec2 cover(vec2 uv, vec2 res, vec2 img){ float rs=res.x/res.y, ri=img.x/img.y;
  vec2 s = rs>ri ? vec2(1., ri/rs) : vec2(rs/ri, 1.); return (uv-.5)*s+.5; }
`;
const QUAD_VS = /* glsl */`varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }`;

const loops = [];
function frame(t) {
  for (let i = 0; i < loops.length; i++) loops[i](t * 0.001);
  requestAnimationFrame(frame);
}

/* =====================================================================
   HERO — liquid cursor lens + dissolve reveal + drifting gold dust
   ===================================================================== */
async function initHero() {
  const canvas = document.getElementById('hero-gl');
  const hero = document.querySelector('.hero');
  const img = document.querySelector('.hero__img');
  if (!canvas || !img) return;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(DPR);
  renderer.setClearColor(0x0f2434, 1);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 40);
  camera.position.z = 5;

  const tex = await loadTex(img.currentSrc || img.src, false);
  const uniforms = {
    uTex: { value: tex }, uRes: { value: new THREE.Vector2(1, 1) },
    uImg: { value: new THREE.Vector2(tex.image.width, tex.image.height) },
    uMouse: { value: new THREE.Vector2(.5, .5) }, uVel: { value: 0 }, uTime: { value: 0 },
    uReveal: { value: reduce ? 1 : 0 }, uScroll: { value: 0 }, uFocus: { value: parseFloat(img.dataset.focus || '0') }
  };
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({
    uniforms, depthTest: false, depthWrite: false, vertexShader: QUAD_VS,
    fragmentShader: /* glsl */`
      precision highp float;
      uniform sampler2D uTex; uniform vec2 uRes, uImg, uMouse; uniform float uVel, uTime, uReveal, uScroll, uFocus;
      varying vec2 vUv; ${NOISE}
      void main(){
        float asp = uRes.x/uRes.y;
        vec2 uv = vUv;
        float zoom = 1.16 - uReveal*.10 + uScroll*.14 + sin(uTime*.12)*.006;
        uv = (uv-.5)/zoom + .5;
        uv += (uMouse-.5)*vec2(-.016,-.012);
        vec2 dm = vUv-uMouse; vec2 dma = dm*vec2(asp,1.);
        float dist = length(dma);
        float lens = exp(-dist*dist*20.)*uVel;
        uv -= dm*lens*.16;
        uv += normalize(dma+1e-5)*sin(dist*36.-uTime*5.)*.004*lens;
        vec2 c = cover(uv, uRes, uImg);
        c.x += (1. - min(1., asp/(uImg.x/uImg.y))) * uFocus; // optional horizontal focus shift on portrait screens
        vec2 off = dm*lens*.045;
        vec3 col = vec3(texture2D(uTex,c+off).r, texture2D(uTex,c).g, texture2D(uTex,c-off).b);
        col *= 1. - uScroll*.5;
        // dissolve reveal, rising from the floor
        vec3 navy = vec3(.059,.141,.204);
        float n = fbm(vUv*vec2(asp,1.)*3.2);
        float v = n*.42 + vUv.y*.58;
        float th = mix(-.15, 1.2, uReveal);
        float m = 1. - smoothstep(th-.14, th, v);
        float edge = exp(-pow((v-th+.02)/.03, 2.)) * (1.-step(.999,uReveal));
        col = mix(navy, col, m) + vec3(.925,.863,.706)*edge*.55;
        col += (hash(vUv*uRes + fract(uTime)*100.) - .5)*.028;
        gl_FragColor = vec4(col,1.);
      }`
  }));
  quad.frustumCulled = false; quad.renderOrder = -1;
  scene.add(quad);

  // dust
  const N = coarse ? 140 : 300;
  const pos = new Float32Array(N * 3), seed = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    pos[i * 3] = (Math.random() - .5) * 13; pos[i * 3 + 1] = (Math.random() - .5) * 8; pos[i * 3 + 2] = (Math.random() - .5) * 7;
    seed[i * 3] = Math.random(); seed[i * 3 + 1] = Math.random(); seed[i * 3 + 2] = Math.random();
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('aSeed', new THREE.BufferAttribute(seed, 3));
  const dustU = { uTime: { value: 0 }, uPx: { value: DPR }, uAlpha: { value: 0 } };
  const dust = new THREE.Points(g, new THREE.ShaderMaterial({
    uniforms: dustU, transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: /* glsl */`
      attribute vec3 aSeed; uniform float uTime, uPx; varying float vA;
      void main(){
        vec3 p = position;
        p.y = mod(p.y + uTime*(.05+aSeed.x*.12) + 4., 8.) - 4.;
        p.x += sin(uTime*(.15+aSeed.y*.3) + aSeed.z*6.28)*.35;
        p.z += cos(uTime*.2 + aSeed.x*6.28)*.25;
        vec4 mv = modelViewMatrix*vec4(p,1.);
        gl_Position = projectionMatrix*mv;
        gl_PointSize = (2. + aSeed.z*5.) * uPx * (5./-mv.z);
        vA = (.25 + .75*abs(sin(uTime*(.4+aSeed.y) + aSeed.x*6.28))) * smoothstep(4.,3.,abs(p.y));
      }`,
    fragmentShader: /* glsl */`
      precision highp float; uniform float uAlpha; varying float vA;
      void main(){ float d = length(gl_PointCoord-.5); float a = smoothstep(.5,0.,d);
        gl_FragColor = vec4(vec3(1.,.9,.7)*a*a*vA*uAlpha*.55, 1.); }`
  }));
  dust.frustumCulled = false;
  scene.add(dust);

  function size() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    uniforms.uRes.value.set(w, h);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  size(); addEventListener('resize', size);

  const mouse = new THREE.Vector2(.5, .5), target = new THREE.Vector2(.5, .5);
  let vel = 0, lastX = .5, lastY = .5;
  hero.addEventListener('pointermove', e => {
    const r = hero.getBoundingClientRect();
    target.set((e.clientX - r.left) / r.width, 1 - (e.clientY - r.top) / r.height);
  });

  let t0 = null, shown = false, visible = true;
  new IntersectionObserver(es => { visible = es[0].isIntersecting; }).observe(hero);

  loops.push(t => {
    if (!visible) return;
    if (!shown) { shown = true; root.classList.add('gl-hero'); }
    if (root.classList.contains('is-ready') && !reduce) {
      if (t0 === null) t0 = t;
      const k = clamp((t - t0 - .15) / 2.2, 0, 1);
      uniforms.uReveal.value = 1 - Math.pow(1 - k, 3);
      dustU.uAlpha.value = clamp((t - t0 - .8) / 2, 0, 1);
    } else if (reduce) dustU.uAlpha.value = 1;
    mouse.lerp(target, .07);
    const sp = Math.hypot(mouse.x - lastX, mouse.y - lastY) * 60; lastX = mouse.x; lastY = mouse.y;
    vel = lerp(vel, clamp(sp, 0, 1), sp > vel ? .2 : .04);
    uniforms.uMouse.value.copy(mouse); uniforms.uVel.value = vel;
    uniforms.uTime.value = t; dustU.uTime.value = t;
    uniforms.uScroll.value = clamp(window.scrollY / hero.offsetHeight, 0, 1);
    camera.position.x = (mouse.x - .5) * .5; camera.position.y = (mouse.y - .5) * .3;
    renderer.render(scene, camera);
  });
}

/* =====================================================================
   PROCESS — scroll-scrubbed sketch → clay model → finished room
   ===================================================================== */
function initProcess() {
  const canvas = document.getElementById('process-gl');
  const section = document.querySelector('.process');
  const view = document.querySelector('.process__view');
  if (!canvas) return;
  let started = false, visible = false;

  async function start() {
    started = true;
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(DPR);
    const scene = new THREE.Scene(), camera = new THREE.Camera();
    const [t0, t1, t2] = await Promise.all(['sketch', 'clay', 'majlis'].map(n => loadTex(`/ah-preview/assets/img/${n}.webp`, false)));
    const u = {
      uT0: { value: t0 }, uT1: { value: t1 }, uT2: { value: t2 },
      uRes: { value: new THREE.Vector2(1, 1) }, uImg: { value: new THREE.Vector2(t2.image.width, t2.image.height) },
      uA: { value: 0 }, uB: { value: 0 }, uMouse: { value: new THREE.Vector2(.5, .5) }, uTime: { value: 0 }
    };
    const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({
      uniforms: u, depthTest: false, vertexShader: QUAD_VS,
      fragmentShader: /* glsl */`
        precision highp float;
        uniform sampler2D uT0,uT1,uT2; uniform vec2 uRes,uImg,uMouse; uniform float uA,uB,uTime;
        varying vec2 vUv; ${NOISE}
        void main(){
          float asp = uRes.x/uRes.y;
          vec2 uv = (vUv-.5)/1.05 + .5 + (uMouse-.5)*vec2(-.012,-.009);
          vec2 c = cover(uv, uRes, uImg);
          vec3 s = texture2D(uT0,c).rgb, m = texture2D(uT1,c).rgb, f = texture2D(uT2,c).rgb;
          float n = fbm(vUv*vec2(asp,1.)*3.4 + 7. + uTime*.02);
          float v = vUv.x*.60 + (1.-vUv.y)*.10 + n*.30;
          float thA = mix(-.1,1.1,uA), thB = mix(-.1,1.1,uB);
          float mA = 1.-smoothstep(thA-.03, thA+.03, v);
          float mB = 1.-smoothstep(thB-.03, thB+.03, v);
          vec3 col = mix(mix(s,m,mA), f, mB);
          float eA = exp(-pow((v-thA)/.006,2.)) * step(.002,uA)*step(uA,.998);
          float eB = exp(-pow((v-thB)/.006,2.)) * step(.002,uB)*step(uB,.998);
          float gA = exp(-pow((v-thA)/.035,2.)) * step(.002,uA)*step(uA,.998);
          float gB = exp(-pow((v-thB)/.035,2.)) * step(.002,uB)*step(uB,.998);
          col += vec3(.925,.863,.706)*(eA+eB)*.5 + vec3(.925,.863,.706)*(gA+gB)*.07;
          col += (hash(vUv*uRes + fract(uTime)*100.) - .5)*.02;
          gl_FragColor = vec4(col,1.);
        }`
    }));
    quad.frustumCulled = false; scene.add(quad);

    function size() {
      const w = view.clientWidth, h = view.clientHeight;
      renderer.setSize(w, h, false); u.uRes.value.set(w, h);
    }
    size(); addEventListener('resize', size);
    const target = new THREE.Vector2(.5, .5);
    section.addEventListener('pointermove', e => { target.set(e.clientX / innerWidth, 1 - e.clientY / innerHeight); });
    let a = 0, b = 0, first = true;
    loops.push(t => {
      if (!visible) return;
      a = lerp(a, AH.process.a, reduce ? 1 : .12); b = lerp(b, AH.process.b, reduce ? 1 : .12);
      u.uA.value = a; u.uB.value = b; u.uTime.value = t;
      u.uMouse.value.lerp(target, .06);
      renderer.render(scene, camera);
      if (first) { first = false; root.classList.add('gl-process'); }
    });
  }
  new IntersectionObserver(es => {
    visible = es[0].isIntersecting;
    if (visible && !started) start().catch(() => {});
  }, { rootMargin: '60% 0px' }).observe(section);
}

/* =====================================================================
   MATERIALS — PBR palette carousel
   ===================================================================== */
function initMaterials() {
  const canvas = document.getElementById('materials-gl');
  const section = document.querySelector('.materials');
  if (!canvas) return;
  let started = false, visible = false;

  async function start() {
    started = true;
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(DPR);
    renderer.setClearColor(0x000000, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.1;
    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x0d2031, 6.8, 11.2);
    const pm = new THREE.PMREMGenerator(renderer);
    scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = .85;
    const camera = new THREE.PerspectiveCamera(32, 1, .1, 40);
    const key = new THREE.DirectionalLight(0xfff0d8, 2.4); key.position.set(4, 6, 6); scene.add(key);
    const rim = new THREE.PointLight(0xee7b62, 30, 20); rim.position.set(-5, 2, -2); scene.add(rim);
    const fill = new THREE.PointLight(0xecdcb4, 14, 20); fill.position.set(3, -2, 4); scene.add(fill);

    const aniso = renderer.capabilities.getMaxAnisotropy();
    const T = async (n, rx, ry) => {
      const t = await loadTex(`/ah-preview/assets/tex/${n}.webp`, true);
      t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); t.anisotropy = aniso; return t;
    };
    const [trav, wal, mar, bou, ver] = await Promise.all([T('travertine', 2, 1), T('walnut', 2, 1), T('marble', 2, 1), T('boucle', 5, 2.5), T('verde', 2, 1)]);

    // brushed brass micro-texture
    const bc = document.createElement('canvas'); bc.width = 512; bc.height = 256;
    const bx = bc.getContext('2d'); bx.fillStyle = '#808080'; bx.fillRect(0, 0, 512, 256);
    for (let i = 0; i < 2600; i++) {
      const v = 90 + Math.random() * 90 | 0; bx.strokeStyle = `rgba(${v},${v},${v},.35)`; bx.lineWidth = Math.random() * 1.2;
      const y = Math.random() * 256, x = Math.random() * 512; bx.beginPath(); bx.moveTo(x, y); bx.lineTo(x + 40 + Math.random() * 180, y); bx.stroke();
    }
    const brushed = new THREE.CanvasTexture(bc); brushed.wrapS = brushed.wrapT = THREE.RepeatWrapping; brushed.repeat.set(2, 3); brushed.anisotropy = aniso;

    const P = o => new THREE.MeshPhysicalMaterial(o);
    const mats = [
      P({ map: trav, bumpMap: trav, bumpScale: 1.2, roughness: .78, metalness: 0 }),
      P({ map: wal, bumpMap: wal, bumpScale: .4, roughness: .42, clearcoat: .35, clearcoatRoughness: .3 }),
      P({ map: mar, roughness: .12, clearcoat: 1, clearcoatRoughness: .05 }),
      P({ color: 0xcaa25c, metalness: 1, roughness: .34, roughnessMap: brushed, bumpMap: brushed, bumpScale: .25 }),
      P({ map: bou, bumpMap: bou, bumpScale: 4, roughness: 1, sheen: 1, sheenRoughness: .6, sheenColor: new THREE.Color(0xfff3dd) }),
      P({ map: ver, roughness: .1, clearcoat: 1, clearcoatRoughness: .04 })
    ];
    const geo = new THREE.SphereGeometry(1, 128, 80);
    // soft contact shadow
    const sc = document.createElement('canvas'); sc.width = sc.height = 128;
    const sx = sc.getContext('2d'), gr = sx.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, 'rgba(0,0,0,.55)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); sx.fillStyle = gr; sx.fillRect(0, 0, 128, 128);
    const shadowMat = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sc), transparent: true, depthWrite: false, fog: true });
    const shadowGeo = new THREE.PlaneGeometry(3.2, 3.2);

    const N = mats.length, R = 3.1, STEP = Math.PI * 2 / N;
    const items = mats.map((m, i) => {
      const grp = new THREE.Group();
      const s = new THREE.Mesh(geo, m); s.rotation.set(.25, i * 1.3, .12); grp.add(s);
      const sh = new THREE.Mesh(shadowGeo, shadowMat); sh.rotation.x = -Math.PI / 2; sh.position.y = -1.22; grp.add(sh);
      scene.add(grp); return { grp, s };
    });

    function size() {
      const w = canvas.clientWidth, h = canvas.clientHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.position.set(0, .35, 6.2 * Math.max(1, 1.02 / camera.aspect));
      camera.lookAt(0, -.05, -.5);
      camera.updateProjectionMatrix();
    }
    size(); addEventListener('resize', size);

    let rot = 0, rotT = 0, drag = false, sx0 = 0, rot0 = 0, moved = 0, intro = 0;
    AH.mat.on.push(i => { // go to nearest equivalent angle
      const cur = Math.round(rotT); let dlt = ((i - cur) % N + N) % N; if (dlt > N / 2) dlt -= N; rotT = cur + dlt;
    });
    canvas.addEventListener('pointerdown', e => { drag = true; moved = 0; sx0 = e.clientX; rot0 = rotT; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', e => {
      if (!drag) return; const dx = e.clientX - sx0; moved = Math.max(moved, Math.abs(dx));
      rotT = rot0 - dx / canvas.clientWidth * 2.4;
    });
    const end = () => { if (!drag) return; drag = false; rotT = Math.round(rotT); AH.setMaterial(((rotT % N) + N) % N); };
    canvas.addEventListener('pointerup', end); canvas.addEventListener('pointercancel', end);
    const tilt = new THREE.Vector2();
    section.addEventListener('pointermove', e => { const r = section.getBoundingClientRect(); tilt.set((e.clientX - r.left) / r.width - .5, (e.clientY - r.top) / r.height - .5); });

    loops.push(t => {
      if (!visible) return;
      intro = lerp(intro, 1, .03);
      rot = lerp(rot, rotT, reduce ? 1 : .085);
      for (let i = 0; i < N; i++) {
        const a = (i - rot) * STEP, it = items[i];
        const front = Math.pow((Math.cos(a) + 1) / 2, 2.2);
        it.grp.position.set(Math.sin(a) * R, Math.sin(t * .7 + i * 1.7) * .05 - (1 - intro) * 1.2, Math.cos(a) * R - R);
        const sc = lerp(.6, 1, front) * lerp(.7, 1, intro); it.grp.scale.setScalar(sc);
        it.grp.visible = Math.cos(a) > -.25;
        if (!reduce) it.s.rotation.y += .0022 + front * .0016;
      }
      camera.position.x = lerp(camera.position.x, tilt.x * .55, .05);
      camera.position.y = lerp(camera.position.y, .35 - tilt.y * .3, .05);
      camera.lookAt(0, -.05, -.5);
      renderer.render(scene, camera);
    });
  }
  new IntersectionObserver(es => {
    visible = es[0].isIntersecting;
    if (visible && !started) start().catch(() => root.classList.add('no-gl'));
  }, { rootMargin: '40% 0px' }).observe(section);
}

/* =====================================================================
   Smooth scroll (desktop only)
   ===================================================================== */
async function initLenis() {
  if (reduce || coarse) return;
  try {
    const { default: Lenis } = await import('https://cdn.jsdelivr.net/npm/lenis@1.1.14/dist/lenis.mjs');
    const lenis = new Lenis({ lerp: .11, anchors: { offset: -80 } });
    loops.push(t => lenis.raf(t * 1000));
    window.AH.lenis = lenis;
  } catch (e) { /* native scroll is fine */ }
}

if (webglOK()) {
  initHero().catch(() => root.classList.remove('gl-hero'));
  initProcess();
  initMaterials();
} else root.classList.add('no-gl');
initLenis();
requestAnimationFrame(frame);
