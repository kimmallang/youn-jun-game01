// Music from the files supplied by the user (Pokémon Sun & Moon Super Music Collection).
// Short effects without a supplied recording retain the game's synthesized sounds.
(() => {
  const base='assets/audio/sun-moon/';
  const tracks={
    town:"1-14. Lillie's Theme.mp3",
    northTown:'1-01. Title Screen.mp3',
    grayCity:"1-14. Lillie's Theme.mp3",
    blueCity:"1-17. Hau's Theme.mp3",
    route:"1-17. Hau's Theme.mp3",
    eastRoute:"1-17. Hau's Theme.mp3",
    graniteTrail:"1-17. Hau's Theme.mp3",
    streamTrail:"1-17. Hau's Theme.mp3",
    center:'1-29. The Pokémon Center.mp3',
    mart:"1-14. Lillie's Theme.mp3",
    gym:'1-01. Title Screen.mp3',
    wildBattle:'1-21. Battle! (Wild Pokémon).mp3',
    gymBattle:'1-25. Battle! (Trainer).mp3',
    giovanniBattle:'2-27. Battle! (Gladion).mp3'
  };
  const jingles={
    caught:'1-15. Caught a Pokémon!.mp3',
    heal:'1-30. Recovery.mp3',
    badge:'1-19. Obtained a Key Item!.mp3',
    victory:'2-05. Victory! (Team Skull).mp3',
    evolution:'1-52. Evolution.mp3'
  };
  const AudioContextClass=window.AudioContext||window.webkitAudioContext;
  const storageKey='younjun.pokemon.audio.v1';
  const supported=typeof Audio==='function';
  let muted=false,unlocked=false,scene='route',musicFile=null,music=null,jingle=null,jingleTimer=null;
  let context,effectBus,noiseBuffer;
  try{muted=localStorage.getItem(storageKey)==='muted'}catch{}
  const url=file=>base+encodeURIComponent(file);

  function initEffects(){
    if(!AudioContextClass||context)return;
    context=new AudioContextClass();
    effectBus=context.createGain();
    effectBus.gain.value=2.4;
    const limiter=context.createDynamicsCompressor();
    limiter.threshold.value=-18;
    limiter.knee.value=12;
    limiter.ratio.value=8;
    limiter.attack.value=.003;
    limiter.release.value=.18;
    effectBus.connect(limiter);
    limiter.connect(context.destination);
    noiseBuffer=context.createBuffer(1,Math.ceil(context.sampleRate*.24),context.sampleRate);
    const samples=noiseBuffer.getChannelData(0);
    for(let i=0;i<samples.length;i++)samples[i]=(Math.random()*2-1)*(1-i/samples.length);
  }
  function resumeMusic(){
    if(!supported||!unlocked||muted||document.hidden||jingle)return;
    if(!music)setScene(scene);
    music?.play().catch(()=>{});
  }
  function unlock(){
    if(muted||!supported)return;
    unlocked=true;
    initEffects();
    context?.resume().catch(()=>{});
    resumeMusic();
  }
  function clearJingle(){
    clearTimeout(jingleTimer);
    jingleTimer=null;
    if(jingle){jingle.onended=null;jingle.pause();jingle.currentTime=0;jingle=null}
  }
  function finishJingle(){clearJingle();resumeMusic()}
  function setScene(next){
    if(!tracks[next])next='route';
    scene=next;
    const file=tracks[next];
    if(musicFile===file&&music)return;
    music?.pause();
    musicFile=file;
    music=new Audio(url(file));
    music.loop=true;
    music.preload='none';
    music.volume=.42;
    if(next==='wildBattle'||next==='gymBattle'||next==='giovanniBattle')clearJingle();
    resumeMusic();
  }
  function setMuted(next){
    muted=Boolean(next);
    try{localStorage.setItem(storageKey,muted?'muted':'on')}catch{}
    if(muted){music?.pause();clearJingle();context?.suspend().catch(()=>{})}
    else unlock();
    return muted;
  }
  function playJingle(kind){
    if(!supported||!unlocked)return;
    clearJingle();
    music?.pause();
    const clip=new Audio(url(jingles[kind]));
    clip.preload='auto';
    clip.volume=.95;
    jingle=clip;
    clip.onended=finishJingle;
    clip.play().catch(finishJingle);
    if(kind==='victory')jingleTimer=setTimeout(finishJingle,5200);
    if(kind==='evolution')jingleTimer=setTimeout(finishJingle,3600);
  }
  function tone(frequency,when,duration,wave,volume,endFrequency){
    const oscillator=context.createOscillator(),envelope=context.createGain();
    oscillator.type=wave;
    oscillator.frequency.setValueAtTime(frequency,when);
    if(endFrequency)oscillator.frequency.exponentialRampToValueAtTime(Math.max(1,endFrequency),when+duration);
    envelope.gain.setValueAtTime(.0001,when);
    envelope.gain.linearRampToValueAtTime(volume,when+Math.min(.012,duration/4));
    envelope.gain.exponentialRampToValueAtTime(.0001,when+duration);
    oscillator.connect(envelope);
    envelope.connect(effectBus);
    oscillator.start(when);
    oscillator.stop(when+duration+.01);
  }
  function noise(when,duration,volume){
    const source=context.createBufferSource(),filter=context.createBiquadFilter(),envelope=context.createGain();
    source.buffer=noiseBuffer;
    filter.type='highpass';
    filter.frequency.value=420;
    envelope.gain.setValueAtTime(volume,when);
    envelope.gain.exponentialRampToValueAtTime(.0001,when+duration);
    source.connect(filter);
    filter.connect(envelope);
    envelope.connect(effectBus);
    source.start(when);
    source.stop(when+duration);
  }
  function play(kind,detail){
    if(muted)return;
    if(jingles[kind]){playJingle(kind);return}
    if(!context||context.state!=='running')return;
    const at=context.currentTime+.005;
    const beep=(frequency,offset,duration,wave='square',volume=.18,endFrequency)=>
      tone(frequency,at+offset,duration,wave,volume,endFrequency);
    switch(kind){
      case 'encounter':beep(220,0,.12,'sawtooth',.18,440);beep(440,.11,.17,'square',.16,660);break;
      case 'sendout':beep(300,0,.11,'sine',.2,680);beep(690,.1,.2,'square',.17,980);noise(at+.08,.08,.09);break;
      case 'move':
        if(detail==='electric'){for(let i=0;i<4;i++)beep(740+i*120,i*.045,.055,'square',.12)}
        else if(detail==='water'||detail==='bubble'){beep(350,0,.18,'sine',.18,700);beep(530,.09,.15,'sine',.12,320)}
        else if(detail==='fire'){noise(at,.18,.14);beep(190,0,.2,'sawtooth',.14,90)}
        else{beep(340,0,.13,'square',.15,120);noise(at+.06,.1,.1)}
        break;
      case 'hit':noise(at,.12,.22);beep(180,0,.12,'sawtooth',.2,65);break;
      case 'guard':beep(520,0,.1,'triangle',.16,740);beep(760,.1,.13,'sine',.12,600);break;
      case 'faint':beep(480,0,.18,'square',.13,260);beep(230,.17,.25,'triangle',.14,75);break;
      case 'throw':beep(330,0,.28,'sine',.18,830);break;
      case 'shake':beep(400,0,.05,'square',.13,250);break;
      case 'escape':beep(660,0,.13,'square',.17,320);beep(300,.14,.15,'square',.15,140);break;
    }
  }
  document.addEventListener('pointerdown',unlock,{capture:true,once:true});
  document.addEventListener('keydown',unlock,{capture:true,once:true});
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden){music?.pause();jingle?.pause();context?.suspend().catch(()=>{})}
    else if(!muted&&unlocked){
      context?.resume().catch(()=>{});
      if(jingle)jingle.play().catch(finishJingle);
      else resumeMusic();
    }
  });
  window.gameAudio={supported,get muted(){return muted},setMuted,setScene,play};
})();
