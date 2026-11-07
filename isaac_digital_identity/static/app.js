/* Portfolio — Cliente sin frameworks. HTML/CSS/JS de autor. */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const id = document.body.dataset.profileId || 'isaac';
  const state = {profile: null, status: null, peer: null, connected: false, negotiating: false, owner: null};
  const el = (id) => document.getElementById(id);
  const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const notify = (message) => {const toast=el('toast');toast.textContent=message;toast.classList.add('show');clearTimeout(notify.timer);notify.timer=setTimeout(()=>toast.classList.remove('show'),3300);};
  const text = (id, value) => {if(el(id)) el(id).textContent = value ?? '';};
  const profileUrl = () => `${(state.status?.qr_base || window.location.origin).replace(/\/$/,'')}/p/${encodeURIComponent(state.profile?.id || id)}`;

  const art = (kind, number = '01') => {
    const shared = `<span class="art-no">FIG / ${escapeHTML(number)}</span><span class="art-corner">ENGINEERING / 2026</span>`;
    if(kind==='weather') return `<div class="project-art art-weather">${shared}<div class="weather-sun"></div><div class="weather-data"><span>DATOS ILUSTRATIVOS</span><strong>24<sup>°C</sup></strong><span>MONITORING / IOT</span></div><div class="weather-hill"></div><div class="weather-hill h2"></div><svg class="weather-chart" viewBox="0 0 180 65" aria-hidden="true"><path d="M0 55 22 42 40 45 63 17 83 23 101 12 125 33 150 20 180 7"/></svg></div>`;
    if(kind==='bio') return `<div class="project-art art-bio">${shared}<div class="bio-crosshair"></div><svg class="fingerprint" viewBox="0 0 220 220" aria-hidden="true"><path d="M110 24C48 24 20 65 20 115M110 37C57 37 34 69 34 116c0 32-4 44-12 59M110 50c-44 0-63 28-63 67 0 45-7 64-18 82M110 62c-36 0-50 23-50 57 0 48-7 69-19 91M110 76c-25 0-36 18-36 42 0 42-5 68-16 92M110 90c-17 0-23 12-23 29 0 40-3 62-12 89M110 104c-8 0-10 7-10 18 0 34-2 56-8 84M110 24c62 0 90 42 90 91M110 37c53 0 77 32 77 79 0 32 4 44 12 59M110 50c44 0 63 28 63 67 0 45 7 64 18 82M110 62c36 0 50 23 50 57 0 48 7 69 19 91M110 76c25 0 36 18 36 42 0 42 5 68 16 92M110 90c17 0 23 12 23 29 0 40 3 62 12 89M110 104c8 0 10 7 10 18 0 34 2 56 8 84"/></svg><span class="bio-label">AUTENTICACIÓN / ESQUEMA</span></div>`;
    return `<div class="project-art art-vibes">${shared}<div class="art-grid"></div><div class="vertical-marker"></div><div class="sensor-disk"><svg viewBox="0 0 230 90" aria-hidden="true"><path d="M0 46 L36 46 L42 40 L49 57 L58 16 L67 74 L78 44 L100 44 L105 28 L114 67 L123 8 L133 82 L142 46 L160 46 L168 34 L176 57 L182 46 L230 46"/></svg></div><div class="sensor-number">SEÑAL ILUSTRATIVA / EN DESARROLLO</div></div>`;
  };

  function renderProfile(profile){
    state.profile=profile;
    document.title = `Portfolio | ${profile.name}`;
    text('heroFirstName',profile.name.split(' ')[0].toUpperCase());
    text('heroName',profile.name);
    text('heroDescription',profile.about);
    text('heroRole',(profile.role||'').toUpperCase());
    text('avatarInitials',profile.initials || 'ID');
    text('profileIdLabel',profile.id.toUpperCase());
    text('plateName',profile.name.toUpperCase());
    text('plateCareer',(profile.subtitle||'').toUpperCase());
    text('aboutText',profile.about);
    text('aboutManifesto',profile.manifesto);
    text('factCity',(profile.location||'MÉXICO').toUpperCase());
    text('factEducation',profile.education?.[0]?.school?.toUpperCase() || 'PROFESSIONAL PROFILE');
    text('languages',profile.languages || 'ESPAÑOL');
    text('agentId',profile.id.toUpperCase());
    text('agentName',`${profile.name.split(' ')[0].toUpperCase()}.AGENT`);
    text('agentDomain',(profile.role||'ENGINEERING').toUpperCase());
    text('selfNode',profile.name.split(' ')[0].toUpperCase());
    $('.node-self .node-circle').textContent=profile.initials || 'ID';
    text('contactEmail',profile.email || 'CONTACTO POR IDENTIFICADOR');
    text('qrName',profile.name.toUpperCase());
    const emailBtn=el('emailButton');
    if(profile.email){ emailBtn.href=`mailto:${encodeURIComponent(profile.email).replace(/%40/g,'@')}`;emailBtn.classList.remove('hide'); }
    else emailBtn.classList.add('hide');
    el('vcardLink').href=`/api/vcard/${encodeURIComponent(profile.id)}`;
    text('qrUrl',profileUrl());
    el('qrImage').src=`/api/qr/${encodeURIComponent(profile.id)}`;
    el('downloadQr').href=`/api/qr/${encodeURIComponent(profile.id)}`;
    el('downloadQr').download=`portfolio-${profile.id}.png`;
    if(profile.photo){
      const image=new Image();image.onload=()=>{el('profilePhoto').src=image.src;el('profilePhoto').hidden=false;el('avatarInitials').hidden=true;};
      image.onerror=()=>{el('profilePhoto').hidden=true;el('avatarInitials').hidden=false;};
      image.src=profile.photo;
    }
    renderProjects(profile.projects||[]);
    renderExperience(profile);
    renderSkills(profile.skills||[]);
  }

  function renderProjects(projects){
    el('projectsGrid').innerHTML=projects.map(p=>`
      <article class="project-card" tabindex="0" role="button" data-project="${escapeHTML(p.id)}" aria-label="Explorar proyecto ${escapeHTML(p.title)}">
        ${art(p.visual,p.number)}
        <div class="project-content"><div class="project-content-top"><span class="project-category">${escapeHTML(p.category)}</span><span class="project-year">${escapeHTML(p.year)}</span></div>
        <h3>${escapeHTML(p.title)}<span class="lime-text"> ↗</span></h3><p>${escapeHTML(p.description)}</p>
        <div class="project-tags">${(p.tags||[]).map(t=>`<span>${escapeHTML(t)}</span>`).join('')}</div>
        <div class="project-open"><span>VER DETALLES</span><span>↗</span></div></div></article>`).join('');
    $$('[data-project]').forEach(card=>{
      const open=()=>openProject(projects.find(p=>p.id===card.dataset.project));
      card.addEventListener('click',open);
      card.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}});
    });
  }

  function renderExperience(profile){
    el('experienceList').innerHTML=(profile.experience||[]).map((job,i)=>`<div class="timeline-item"><span class="timeline-date">${escapeHTML(job.dates)}</span><h3>${escapeHTML(job.company)}</h3><h4>${escapeHTML(job.position)}</h4><p>${escapeHTML(job.desc)}</p></div>`).join('')||`<div class="timeline-item"><h3>Perfil profesional</h3><p>Intercambio de habilidades y oportunidades.</p></div>`;
    const studies=[...(profile.education||[]).map(x=>({title:x.school,sub:x.degree,time:x.dates})),...(profile.certifications||[]).map(x=>({title:x.name,sub:x.issuer,time:x.dates}))];
    el('educationList').innerHTML=studies.map(s=>`<div class="edu-item"><span>${escapeHTML(s.time)}</span><strong>${escapeHTML(s.title)}</strong><p>${escapeHTML(s.sub)}</p></div>`).join('')||`<div class="edu-item"><p>Información educativa por completar.</p></div>`;
  }

  function renderSkills(groups){
    el('skillsList').innerHTML=groups.map((group,i)=>`<div class="skill-row"><span class="skill-num">0${i+1}</span><span class="skill-name">${escapeHTML(group.name)}</span><div class="skill-tags">${(group.items||[]).map(t=>`<span>${escapeHTML(t)}</span>`).join('')}</div></div>`).join('');
  }

  function openProject(project){
    if(!project)return;
    text('modalProjectCategory',`${project.category} / ${project.year}`);
    el('modalProjectArt').innerHTML=art(project.visual,project.number);
    text('modalProjectTitle',project.title);
    text('modalProjectDescription',project.detail || project.description);
    el('modalProjectTags').innerHTML=(project.tags||[]).map(x=>`<span>${escapeHTML(x)}</span>`).join('');
    text('modalProjectStatus',project.outcome||'PROYECTO');
    el('projectDialog').showModal();
  }

  function renderStatus(){
    const ready=!!state.status?.ai_ready;
    const authorized=!!state.owner?.authenticated;
    const ownerPage=id===state.status?.owner_id;
    text('agentStatus',ready?'✳ CONFIGURADO · SIN VALIDAR':'◌ IA SIN CONFIGURAR');
    el('agentStatus').classList.toggle('offline',!ready);
    text('agentModel',(state.status?.model||'GEMINI').toUpperCase());
    text('ownerAccessStatus',authorized?'Sesión del propietario activa.':'Acceso exclusivo del propietario.');
    el('ownerLoginButton').hidden=authorized || !state.owner?.configured;
    el('ownerLogoutButton').hidden=!authorized;
    el('connectBtn').disabled=!authorized || !ownerPage || state.negotiating;
    el('openCreatePeer').disabled=!authorized || !ownerPage || state.negotiating;
    el('negotiateBtn').disabled=!ready || !authorized || !ownerPage || !state.connected || state.negotiating;
    text('networkHint',!state.owner?.configured?'El acceso privado no está configurado. Consulta la guía de la etapa 1.':!authorized?'Inicia sesión como propietario para usar la demostración local.':!ownerPage?'La demostración se inicia desde el portfolio del propietario.':!ready?'Configura GEMINI_API_KEY en el servidor para activar la demostración local.':state.connected?'Demostración local: los perfiles se enviarán a Gemini en este servidor.':'Conecta un perfil invitado de esta instancia. No hay comunicación federada.');
  }

  async function refreshOwner(){
    const response=await fetch('/api/owner/session',{cache:'no-store'});
    if(!response.ok)throw Error('No se pudo comprobar el acceso del propietario.');
    state.owner=await response.json();
  }

  async function ownerFetch(url,body){
    const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':state.owner?.csrf_token||''},body:JSON.stringify(body)});
    if(response.status===401 || response.status===403){
      await refreshOwner();renderStatus();
    }
    return response;
  }

  async function ownerLogin(event){
    event.preventDefault();
    const password=el('ownerPassword');
    const button=el('ownerLoginForm').querySelector('[type=submit]');
    button.disabled=true;text('ownerLoginError','');
    try{
      await refreshOwner();
      const response=await ownerFetch('/api/owner/login',{password:password.value});
      password.value='';
      const result=await response.json();
      if(!response.ok)throw Error(result.error||'No se pudo iniciar sesión.');
      state.owner=result;renderStatus();el('ownerDialog').close();notify('Sesión del propietario iniciada.');
    }catch(error){password.value='';text('ownerLoginError',error.message);}
    finally{button.disabled=false;}
  }

  async function ownerLogout(){
    try{
      const response=await ownerFetch('/api/owner/logout',{});
      const result=await response.json();
      if(!response.ok)throw Error(result.error||'No se pudo cerrar la sesión.');
      state.peer=null;state.connected=false;
      el('agentLog').innerHTML='';el('peerInput').value='';
      text('peerNode','AWAITING PEER');text('peerNodeInitials','?');text('connectionStatus','NO CONECTADO');
      el('connectionStatus').classList.remove('connected');$('.connection-visual').classList.remove('connected-nodes');
      await refreshOwner();renderStatus();notify('Sesión cerrada.');
    }catch(error){notify(error.message);}
  }

  function peerIdFromInput(raw){
    raw=raw.trim();
    let result=raw;
    if(raw.includes('/p/')){
      try{const url=new URL(raw,window.location.origin);if(url.origin!==window.location.origin)return '';result=url.pathname.split('/p/')[1]?.split('/')[0]||'';}catch{result='';}
    }
    return /^[a-z0-9-]{1,42}$/i.test(result)?result.toLowerCase():'';
  }

  async function connectPeer(raw){
    const peerId=peerIdFromInput(raw);
    if(!peerId){notify('Introduce un ID o URL de perfil válida.');return;}
    if(peerId===id){notify('Necesitas otro perfil distinto al tuyo.');return;}
    if(!state.owner?.authenticated){notify('Inicia sesión como propietario.');return;}
    if(state.negotiating){notify('Espera a que termine la negociación actual.');return;}
    const button=el('connectBtn');button.disabled=true;button.textContent='CONECTANDO...';
    try{
      const requestPeer=await fetch(`/api/profile/${encodeURIComponent(peerId)}`);
      if(!requestPeer.ok)throw Error('No encontré ese perfil. Pídele a tu compañero su ID o crea uno.');
      const peer=await requestPeer.json();
      const response=await ownerFetch('/api/connections',{a:id,b:peerId});
      const result=await response.json();
      if(!response.ok)throw Error(result.error||'No se pudo conectar');
      state.peer=peer;state.connected=true;
      el('peerInput').value=peer.id;
      el('peerNodeInitials').textContent=peer.initials;
      text('peerNode',peer.name.split(' ')[0].toUpperCase());
      text('connectionStatus','● LINK ACTIVE');
      el('connectionStatus').classList.add('connected');
      $('.connection-visual').classList.add('connected-nodes');
      el('agentLog').innerHTML=`<div class="empty-log"><span>✓</span><strong>LINK ESTABLISHED.</strong><p>${escapeHTML(state.profile.name)} y ${escapeHTML(peer.name)} están conectados. Puedes iniciar una negociación entre agentes.</p></div>`;
      renderStatus();notify(`Conectado con ${peer.name}`);
    }catch(error){notify(error.message);}
    finally{button.disabled=false;button.innerHTML='Conectar ↗';}
  }

  function appendLog(entry,kind){
    const log=el('agentLog');if($('.empty-log'))log.innerHTML='';
    const box=document.createElement('div');box.className=`log-entry ${kind==='peer'?'peer':''}`;
    const meta=document.createElement('div');meta.className='log-meta';meta.textContent=`AGENT ${kind==='peer'?'B':'A'} / ${entry.name}`;
    const p=document.createElement('p');p.textContent=entry.text;
    box.append(meta,p);log.append(box);log.scrollTop=log.scrollHeight;
  }

  function showProposal(data){
    const log=el('agentLog');
    const container=document.createElement('div');container.className='proposal-card';
    const title=document.createElement('div');title.className='proposal-label';title.textContent='✳ PROPOSED COLLABORATION / SYNTHESIS';
    const paragraph=document.createElement('p');paragraph.textContent=data.text;
    const status=document.createElement('small');status.textContent=data.status;
    container.append(title,paragraph,status);log.append(container);log.scrollTop=log.scrollHeight;
  }

  async function negotiate(){
    if(state.negotiating || !state.owner?.authenticated || !state.connected || !state.status?.ai_ready)return;
    state.negotiating=true;renderStatus();el('agentLog').innerHTML='';
    const working=document.createElement('div');working.className='log-working';working.id='working';working.textContent='◌ ESTABLECIENDO COMUNICACIÓN ENTRE AGENTES...';el('agentLog').append(working);
    try{
      const response=await ownerFetch('/api/agents/negotiate',{a:id,b:state.peer.id,demo_consent:true});
      if(!response.ok){const error=await response.json();throw Error(error.error||`Error HTTP ${response.status}`);}
      if(!response.body)throw Error('Tu navegador no admite respuestas transmitidas en vivo.');
      const reader=response.body.getReader();const decoder=new TextDecoder();let pending='';let completed=false;
      while(true){
        const {value,done}=await reader.read();if(done)break;
        pending+=decoder.decode(value,{stream:true}).replace(/\r\n/g,'\n');
        let cut;
        while((cut=pending.indexOf('\n\n'))>=0){
          const block=pending.slice(0,cut);pending=pending.slice(cut+2);
          const event=block.match(/^event: (.+)$/m)?.[1];const json=block.match(/^data: (.+)$/m)?.[1];
          if(!event||!json)continue;
          let payload;try{payload=JSON.parse(json);}catch{continue;}
          if(event==='turn'){
            const w=el('working');if(w)w.remove();
            appendLog(payload,payload.agent===id?'self':'peer');
            const indicator=document.createElement('div');indicator.id='working';indicator.className='log-working';indicator.textContent=`◌ AGENT ${payload.step%2===0?'A':'B'} ESTÁ ANALIZANDO LA PROPUESTA...`;
            el('agentLog').append(indicator);el('agentLog').scrollTop=el('agentLog').scrollHeight;
          }else if(event==='proposal'){
            el('working')?.remove();showProposal(payload);
          }else if(event==='error')throw Error(payload.error||'Fallo de comunicación');
          else if(event==='end'){completed=true;el('working')?.remove();}
        }
      }
      if(!completed)throw Error('La transmisión se interrumpió antes de finalizar.');
      notify('Negociación completada. Propuesta pendiente de aprobación humana.');
    }catch(error){el('working')?.remove();appendLog({name:'SISTEMA',text:`ERROR REAL: ${error.message}`},'peer');notify('No se completó la negociación. Revisa la configuración.');}
    finally{state.negotiating=false;renderStatus();}
  }

  async function createPeer(event){
    event.preventDefault();const form=el('peerForm');const button=form.querySelector('[type=submit]');
    const values=Object.fromEntries(new FormData(form).entries());
    values.skills=values.skills.split(',').map(x=>x.trim()).filter(Boolean);
    text('peerFormError','');button.disabled=true;button.textContent='CREANDO...';
    try{
      const response=await ownerFetch('/api/profiles',values);
      const result=await response.json();if(!response.ok)throw Error(result.error||'No se creó el perfil.');
      el('peerDialog').close();form.reset();notify(`Identidad ${result.profile.id} creada.`);await connectPeer(result.profile.id);
    }catch(error){text('peerFormError',error.message);}
    finally{button.disabled=false;button.innerHTML='Crear y conectar <span>↗</span>';}
  }

  function bindEvents(){
    $$('[data-jump]').forEach(b=>b.addEventListener('click',()=>el(b.dataset.jump)?.scrollIntoView({behavior:'smooth'})));
    el('openQrHero').addEventListener('click',()=>el('qrDialog').showModal());
    el('openQrAgent').addEventListener('click',()=>el('qrDialog').showModal());
    el('openCreatePeer').addEventListener('click',()=>el('peerDialog').showModal());
    $$('[data-close]').forEach(b=>b.addEventListener('click',()=>el(b.dataset.close).close()));
    $$('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d)d.close();}));
    el('copyProfileUrl').addEventListener('click',async()=>{
      try{await navigator.clipboard.writeText(profileUrl());notify('Enlace copiado al portapapeles.');}
      catch{notify('Copia el enlace que aparece debajo del QR.');}
    });
    el('connectBtn').addEventListener('click',()=>connectPeer(el('peerInput').value));
    el('peerInput').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();connectPeer(el('peerInput').value);}});
    el('negotiateBtn').addEventListener('click',negotiate);
    el('peerForm').addEventListener('submit',createPeer);
    el('ownerLoginButton').addEventListener('click',()=>el('ownerDialog').showModal());
    el('ownerLogoutButton').addEventListener('click',ownerLogout);
    el('ownerLoginForm').addEventListener('submit',ownerLogin);
    el('ownerDialog').addEventListener('close',()=>{el('ownerPassword').value='';text('ownerLoginError','');});
    const nav=el('mobileNav'),toggle=el('mobileMenu');
    toggle.addEventListener('click',()=>{nav.classList.toggle('open');toggle.setAttribute('aria-expanded',nav.classList.contains('open'));});
    $$('#mobileNav a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');}));
    document.addEventListener('scroll',()=>{const height=document.documentElement.scrollHeight-window.innerHeight;el('scrollProgress').style.width=`${height>0?100*window.scrollY/height:0}%`;},{passive:true});
  }

  async function init(){
    bindEvents();
    try{
      const [profileRes,statusRes]=await Promise.all([fetch(`/api/profile/${encodeURIComponent(id)}`),fetch('/api/status',{cache:'no-store'})]);
      if(!profileRes.ok)throw Error('No se pudo cargar el perfil');
      if(!statusRes.ok)throw Error('No se pudo comprobar la configuración del agente');
      state.status=await statusRes.json();renderProfile(await profileRes.json());
      try{await refreshOwner();}catch(error){notify(error.message);}
      renderStatus();
    }catch(error){notify(`No se pudieron cargar los datos: ${error.message}`);}
  }
  init();
})();
