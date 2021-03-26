var holdings={{session['portfolio']|safe}}

function formatMoney(number, curr, n=2) {
  return number.toLocaleString('en-US', { style: 'currency', currency: curr, minimumFractionDigits:n, maximumFractionDigits:n });
}

function isItNumber(str) {
  return /^\-?[0-9]+(e[0-9]+)?(\.[0-9]+)?$/.test(str);
}

function FormatMoneyChange(e, curr){ //where e is element. note that this regex matching cannot process commas in the number - number to be formatted MUST BE in standard number form without currency commas
  var re = /-?\d+\.\d+/g;
  var tmp=parseFloat(e.innerHTML.match(re) );
  if(tmp>0){
    e.innerHTML="&#x25B2;".concat( formatMoney(tmp, curr) );
    e.classList.remove("loss");
    e.classList.remove('neutral');
    e.classList.add("gain");
  }
  else if(tmp<0){
    e.innerHTML="&#x25BC;".concat( formatMoney( Math.abs(tmp), curr) );
    e.classList.remove("gain");
    e.classList.remove('neutral');
    e.classList.add("loss");
  }
  else if(tmp==0){
      e.innerHTML=formatMoney(0, curr);
      e.classList.remove("gain");
      e.classList.remove('loss');
      e.classList.add('neutral');
  }
}

function FormatMoneyAmount(curr){
  var a=document.getElementsByClassName("money_amount_only");
  for(var i=0; i<a.length; i++){
    var tmp=a[i].innerHTML;
    a[i].innerHTML=formatMoney( parseFloat(tmp), curr);
  }

  var b = document.getElementsByClassName("money_amount_change_figure");
  //var re = /\d+\.\d+/g;
  //var re = /\d+\.\d+/g;
  var re = /-?\d+\.\d+/g;
  for(var i=0; i<b.length; i++){
    FormatMoneyChange(b[i], curr)
  }
}

function FormatDashboardStocks(){
  var re = /-?\d+\.\d+/g;
  var table=document.getElementById("dashboard_stocks");
  for(var i=1, row; row=table.rows[i]; i++){
    if(i!=0){
      var curr='INR';
      var tmp=0;
      for( var j=0, col; col=row.cells[j]; j++){
        if(j==1){
          curr=col.innerHTML;
        }
        else if(j==3||j==4||j==5){
          tmp=col.innerHTML;
          col.innerHTML=formatMoney(parseFloat(tmp), curr);
        }
        else if(j==6){
          FormatMoneyChange(col, curr)
        }
      }
    }
  }
}
function UpdateCurrencyTable(){
  var table = document.getElementById("currency_table");
  for (var i = 1, row; row = table.rows[i]; i++) {
     //iterate through rows
     //rows would be accessed using the "row" variable assigned in the for loop
     var currency='INR';
     for (var j = 0, col; col = row.cells[j]; j++)
     {
       //iterate through columns
       //columns would be accessed using the "col" variable assigned in the for loop
       if(i!=0){
         if(j==0){
         currency=col.innerHTML;
        }
        else if(j>1){
          col.innerHTML=formatMoney( parseFloat( col.innerHTML), currency)

        }
     }
    }
  }
}

var last_forex_update="normal";

function UpdateThings_FOREX_FULL(){
  if(last_forex_update=="normal"){
    UpdateThings_FOREX();
  }
  else if(last_forex_update=="reverse"){
    UpdateThings_FOREX_REVERSE();
  }
}

function UpdateThings_FOREX(){
  var purch_button= document.getElementById('purchase');
  var a = document.getElementById('from_currency');
  var b = document.getElementById("cash_in_hand_FROMCURR");
  var c = document.getElementById('to_currency');
  var d = document.getElementById("cash_in_hand_TOCURR");
  b.innerHTML= formatMoney( portfolio_data['currency_holding'][a.value], a.options[a.selectedIndex].text );
  d.innerHTML= formatMoney( portfolio_data['currency_holding'][c.value], c.options[c.selectedIndex].text);
  a_ = Math.min(a.value, c.value);
  c_ = Math.max(a.value, c.value);
  exch_rate=1;
  if(a_==a.value && c_==c.value ){
    exch_rate = rates[a_][c_];
  }
  else{
    exch_rate= (1 / (rates[a_][c_]) );
  }
  var e=document.getElementById("exch_rate");
  e.innerHTML = formatMoney(exch_rate , c.options[c.selectedIndex].text).concat(' per ', formatMoney(1, a.options[a.selectedIndex].text) );
  var f = document.getElementById("amount").value;
  f = f.replace(",", "");
  document.getElementById('amount').value = f;
  var is_a_num = isItNumber(f);
  var is_empty = !f.length;
  if(!is_a_num || isNaN(parseFloat(f))){
    f=0;
  }
  f = parseFloat(f);
  var g=document.getElementById("amount_reverse");
  //g.innerHTML= formatMoney(f*exch_rate, c.options[c.selectedIndex].text );
  g.value = f*exch_rate;
  insuff_funds=document.getElementById('insuffFunds');
  var have_suff_funds =  ( f <= portfolio_data['currency_holding'][a.value] );
  var xa_str="&nbsp;";
  if( !have_suff_funds || a.value==c.value || f==0 || !is_a_num){ //if insufficient funds or converting to same currency
    purch_button.disabled=true;
    purch_button.classList.add('disabled');
    if(!have_suff_funds) {
      xa_str = xa_str.concat("Insufficient Funds!\n");
    }
    if(!is_a_num && !is_empty){
      xa_str = xa_str.concat("Not a number!");
    }
  }
  else{
    purch_button.disabled=false;
    purch_button.classList.remove('disabled');
  }
  insuff_funds.innerHTML=xa_str;
  var summary_L = document.getElementById("summary_from_curr_name");
  var summary_M = document.getElementById("summary_from_curr_cashinhand");
  var summary_N = document.getElementById("summary_to_curr_name");
  var summary_O = document.getElementById("summary_to_curr_cashinhand");
  summary_L.innerHTML= a.options[a.selectedIndex].text;
  summary_M.innerHTML = formatMoney( portfolio_data['currency_holding'][a.value], a.options[a.selectedIndex].text );
  summary_N.innerHTML=c.options[c.selectedIndex].text;
  summary_O.innerHTML = formatMoney( portfolio_data['currency_holding'][c.value], c.options[c.selectedIndex].text);


  if(a.value != c.value){
    document.getElementById("summary_from_curr_netchange").innerHTML = formatMoney(f, a.options[a.selectedIndex].text);
    document.getElementById("summary_from_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][a.value]-f, a.options[a.selectedIndex].text);
    document.getElementById("summary_to_curr_netchange").innerHTML = formatMoney(f*exch_rate, c.options[c.selectedIndex].text);
    document.getElementById("summary_to_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][c.value]+(f*exch_rate), c.options[c.selectedIndex].text);
  }
  else{
    document.getElementById("summary_from_curr_netchange").innerHTML = formatMoney(0, a.options[a.selectedIndex].text);
    document.getElementById("summary_from_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][a.value], a.options[a.selectedIndex].text);
    document.getElementById("summary_to_curr_netchange").innerHTML = formatMoney(0, c.options[c.selectedIndex].text);
    document.getElementById("summary_to_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][c.value], c.options[c.selectedIndex].text);
  }
  last_forex_update="normal";
  return 1;
}

function UpdateThings_FOREX_REVERSE(){
  var purch_button= document.getElementById('purchase');
  var a = document.getElementById('from_currency');
  var b = document.getElementById("cash_in_hand_FROMCURR");
  var c = document.getElementById('to_currency');
  var d = document.getElementById("cash_in_hand_TOCURR");
  b.innerHTML= formatMoney( portfolio_data['currency_holding'][a.value], a.options[a.selectedIndex].text );
  d.innerHTML= formatMoney( portfolio_data['currency_holding'][c.value], c.options[c.selectedIndex].text);
  a_ = Math.min(a.value, c.value);
  c_ = Math.max(a.value, c.value);
  exch_rate=1;
  if(a_==a.value && c_==c.value ){
    exch_rate = rates[a_][c_];
  }
  else{
    exch_rate= (1 / (rates[a_][c_]) );
  }
  var e=document.getElementById("exch_rate");
  e.innerHTML = formatMoney(exch_rate , c.options[c.selectedIndex].text).concat(' per ', formatMoney(1, a.options[a.selectedIndex].text) );
  var f = document.getElementById("amount_reverse").value;
  f = f.replace(",", "");
  document.getElementById('amount_reverse').value = f;
  var is_a_num = isItNumber(f);
  var is_empty = !f.length;
  if(!is_a_num || isNaN(parseFloat(f))){
    f=0;
  }
  f = parseFloat(f);
  var g=document.getElementById("amount");
  //g.innerHTML= formatMoney(f*exch_rate, c.options[c.selectedIndex].text );
  g.value = f*(1/exch_rate);
  insuff_funds=document.getElementById('insuffFunds');
  var have_suff_funds =  ( g.value <= portfolio_data['currency_holding'][a.value] );
  var xa_str="&nbsp;";
  if( !have_suff_funds || a.value==c.value || f==0 || !is_a_num){ //if insufficient funds or converting to same currency
    purch_button.disabled=true;
    purch_button.classList.add('disabled');
    if(!have_suff_funds) {
      xa_str = xa_str.concat("Insufficient Funds!\n");
    }
    if(!is_a_num && !is_empty){
      xa_str = xa_str.concat("Not a number!");
    }
  }
  else{
    purch_button.disabled=false;
    purch_button.classList.remove('disabled');
  }
  insuff_funds.innerHTML=xa_str;
  var summary_L = document.getElementById("summary_from_curr_name");
  var summary_M = document.getElementById("summary_from_curr_cashinhand");
  var summary_N = document.getElementById("summary_to_curr_name");
  var summary_O = document.getElementById("summary_to_curr_cashinhand");
  summary_L.innerHTML= a.options[a.selectedIndex].text;
  summary_M.innerHTML = formatMoney( portfolio_data['currency_holding'][a.value], a.options[a.selectedIndex].text );
  summary_N.innerHTML=c.options[c.selectedIndex].text;
  summary_O.innerHTML = formatMoney( portfolio_data['currency_holding'][c.value], c.options[c.selectedIndex].text);


  if(a.value != c.value){
    document.getElementById("summary_from_curr_netchange").innerHTML = formatMoney(f*(1/exch_rate), a.options[a.selectedIndex].text);
    document.getElementById("summary_from_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][a.value]-(f*(1/exch_rate) ), a.options[a.selectedIndex].text);
    document.getElementById("summary_to_curr_netchange").innerHTML = formatMoney(f, c.options[c.selectedIndex].text);
    document.getElementById("summary_to_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][c.value]+(f), c.options[c.selectedIndex].text);
  }
  else{
    document.getElementById("summary_from_curr_netchange").innerHTML = formatMoney(0, a.options[a.selectedIndex].text);
    document.getElementById("summary_from_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][a.value], a.options[a.selectedIndex].text);
    document.getElementById("summary_to_curr_netchange").innerHTML = formatMoney(0, c.options[c.selectedIndex].text);
    document.getElementById("summary_to_curr_cashleft").innerHTML = formatMoney(portfolio_data['currency_holding'][c.value], c.options[c.selectedIndex].text);
  }
  last_forex_update="reverse";
  return 1;
}
