/* Compare page: fills the attribute matrix and highlights differing rows.
   The matrix itself arrives as JSON in #cmp-matrix (json_script), which is
   safer than interpolating it into a script body. */
// Fill matrix values
const matrix = JSON.parse(document.getElementById('cmp-matrix').textContent);
document.querySelectorAll('.attr-val').forEach(el=>{
  const attr=el.dataset.attr;
  const pid=el.dataset.product;
  if(matrix[attr]&&matrix[attr][pid]){ el.textContent=matrix[attr][pid]; }
});

function removeFromCompare(pid){
  let items=JSON.parse(localStorage.getItem('tzCompare')||'[]');
  items=items.filter(p=>p.id!==pid);
  localStorage.setItem('tzCompare',JSON.stringify(items));
  if(items.length===0){ window.location.href='/products/'; }
  else {
    const ids=items.map(p=>'ids='+p.id).join('&');
    window.location.href='/products/compare/?'+ids;
  }
}
function clearAllCompare(){
  localStorage.setItem('tzCompare','[]');
  window.location.href='/products/';
}
