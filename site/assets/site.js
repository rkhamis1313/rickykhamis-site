
(function(){
  var yr=document.getElementById('yr');if(yr)yr.textContent=new Date().getFullYear();
  document.querySelectorAll('.nav > li > button').forEach(function(b){
    b.addEventListener('click',function(e){e.stopPropagation();var li=b.parentNode,open=li.classList.contains('open');
      document.querySelectorAll('.nav > li.open').forEach(function(x){x.classList.remove('open');x.querySelector('button').setAttribute('aria-expanded','false')});
      if(!open){li.classList.add('open');b.setAttribute('aria-expanded','true')}});
  });
  document.addEventListener('click',function(){document.querySelectorAll('.nav > li.open').forEach(function(x){x.classList.remove('open')})});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){document.querySelectorAll('.nav > li.open').forEach(function(x){x.classList.remove('open')});closeM()}});
  var m=document.getElementById('mnav');function closeM(){m.classList.remove('open');document.body.style.overflow=''}
  document.getElementById('burger').addEventListener('click',function(){m.classList.add('open');document.body.style.overflow='hidden'});
  document.getElementById('mclose').addEventListener('click',closeM);
  m.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){b.nextElementSibling.classList.toggle('open')})});
})();
