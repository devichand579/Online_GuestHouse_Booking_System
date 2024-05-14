document.addEventListener("DOMContentLoaded", e => {
  let card_number_input = document.querySelector("form fieldset.card-number input"),
      card_number_display = document.querySelector("div#card .card-number");

  let card_holder_input = document.querySelector("form fieldset.card-holder input"),
      card_holder_display = document.querySelector("div#card .card-holder > span:nth-child(2)");

  let expiry_month_select = document.querySelector("form fieldset.expiry-month > select"),
      expiry_month_display = document.querySelector("div#card .expiry span.expiry-month");

  let expiry_year_select = document.querySelector("form fieldset.expiry-year > select"),
      expiry_year_display = document.querySelector("div#card .expiry span.expiry-year");

  let cvc_input = document.querySelector("form fieldset.cvc input"),
      cvc_display = document.querySelector("div#card .cvc > span:nth-child(2)");

  let form = document.querySelector("form");

  card_number_input.onkeydown = e => {
    let key = e.keyCode || e.charCode;

    let is_digit = (key >= 48 && key <= 57) || (key >= 96 && key <= 105);
    let is_delete = key == 8 || key == 46;

    if (is_digit || is_delete) {
      let text = e.target.value;
      let len = text.length;

      if(is_digit && (len==4 || len==9 || len==14))
        card_number_input.value = text + " ";
    }
    else return false;
  }

  card_number_input.onkeyup = e => {
    let key = e.keyCode || e.charCode;

    let is_digit = (key >= 48 && key <= 57) || (key >= 96 && key <= 105);
    let is_delete = key == 8 || key == 46;

    if (is_digit || is_delete) {
      let text = e.target.value;
      let len = text.length;
      let digits = "XXXX XXXX XXXX XXXX".split('');

      if(is_digit && (len==4 || len==9 || len==14))
        digits[len] = " ";

      for(let i=0;i<len;i++)
        digits[i] = text.charAt(i);

      card_number_display.innerText = digits.join('');
    }
    else return false;
  }

  card_holder_input.onkeyup = e => {
    card_holder_display.innerText = e.target.value;
  }

  expiry_month_select.onchange = e => {
    if(!e.target.value) expiry_month_display.innerText = "00";
    expiry_month_display.innerText = e.target.value;
  }

  expiry_year_select.onchange = e => {
    if(!e.target.value) expiry_year_display.innerText = "00";
    expiry_year_display.innerText = e.target.value;
  }

  cvc_input.onkeyup = e => {
    let text = e.target.value;
    let digits = ['_','_','_'];

    for(let i=0;i<text.length;i++)
      digits[i] = text.charAt(i);

    cvc_display.innerText = digits.join('');
  }

  form.onsubmit = e => {
    e.preventDefault();
  }
});


